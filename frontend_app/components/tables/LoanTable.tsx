'use client'

import { useState, useEffect } from 'react'
import { useDrillDown } from '@/lib/drill-down-context'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ChevronRight, Filter } from 'lucide-react'

interface Loan {
  loan_id: string
  product_type: string
  current_balance: number
  interest_rate: number
  payment_status: string
  borrower_name: string
  origination_date: string
}

interface LoanTableProps {
  filters?: Record<string, any>
  onLoanClick?: (loanId: string) => void
  type?: 'loans' | 'deposits'
}

export default function LoanTable({ filters = {}, onLoanClick, type = 'loans' }: LoanTableProps) {
  const [loans, setLoans] = useState<Loan[]>([])
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    // Fetch loans or deposits with filters
    const queryParams = new URLSearchParams()

    if (filters.product_type) {
      queryParams.append('product_type', filters.product_type)
    }
    if (filters.days) {
      queryParams.append('days', filters.days.toString())
    }

    setLoading(true)
    const endpoint = type === 'loans' ? 'loans' : 'deposits'
    fetch(`http://localhost:8000/api/data/${endpoint}?${queryParams}`)
      .then(res => res.json())
      .then(data => {
        setLoans(data[type] || [])
        setLoading(false)
      })
      .catch(err => {
        console.error(`Error loading ${type}:`, err)
        setLoading(false)
      })
  }, [filters, type])

  const handleLoanClick = (loan: Loan) => {
    // Only open detail panel for loans, not deposits
    if (type === 'loans' && onLoanClick) {
      onLoanClick(loan.loan_id)
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      'Current': 'bg-bloomberg-surface text-bloomberg-green border-2 border-bloomberg-green',
      'Past_Due_30': 'bg-bloomberg-surface text-bloomberg-amber border-2 border-bloomberg-amber',
      'Past_Due_60': 'bg-bloomberg-surface text-bloomberg-orange border-2 border-bloomberg-orange',
      'Past_Due_90': 'bg-bloomberg-surface text-bloomberg-red border-2 border-bloomberg-red',
      'Default': 'bg-bloomberg-surface text-bloomberg-red border-2 border-bloomberg-red'
    }
    return colors[status] || 'bg-bloomberg-surface text-bloomberg-text-dim border-2 border-bloomberg-border'
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-12 bg-bloomberg-surface rounded-none" />
        <div className="h-96 bg-bloomberg-surface rounded-none" />
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center justify-between bg-bloomberg-surface rounded-none border-2 border-bloomberg-border p-4 hover:border-bloomberg-orange/50 transition-colors">
        <div className="flex items-center gap-2 text-sm text-bloomberg-text-dim">
          <Filter className="h-4 w-4" />
          <span className="font-bold font-mono">{loans.length.toLocaleString()} {type === 'loans' ? 'LOANS' : 'DEPOSITS'}</span>
          {filters.product_type && (
            <Badge variant="outline" className="bg-bloomberg-surface border-bloomberg-orange text-bloomberg-orange font-mono">
              {filters.product_type}
            </Badge>
          )}
        </div>

        {/* Product type filter buttons */}
        <div className="flex gap-2">
          {(type === 'loans'
            ? ['C&I', 'Commercial_RE', 'Residential_Mortgage', 'Consumer_Auto']
            : ['DDA', 'MMDA', 'Savings', 'CD', 'NOW']
          ).map(productType => (
            <button
              key={productType}
              onClick={() => {
                const view = type === 'loans' ? 'loan-table' : 'deposit-table'
                navigateTo(view, { product_type: productType }, `${productType} ${type === 'loans' ? 'Loans' : 'Deposits'}`)
              }}
              className={`text-xs px-3 py-1.5 rounded-none border-2 transition-colors font-mono font-bold ${
                filters.product_type === productType
                  ? 'bg-bloomberg-orange text-black border-bloomberg-orange'
                  : 'bg-bloomberg-surface text-bloomberg-text border-bloomberg-border hover:border-bloomberg-orange hover:text-bloomberg-orange'
              }`}
            >
              {productType.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="border-2 border-bloomberg-border rounded-none overflow-hidden bg-bloomberg-surface shadow-xl">
        <Table>
          <TableHeader>
            <TableRow className="bg-bloomberg-surface border-b-2 border-bloomberg-orange/30">
              <TableHead className="text-bloomberg-orange font-mono font-bold">Loan ID</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Borrower</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Product</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Balance</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Rate</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Status</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Originated</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {loans.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} className="text-center text-bloomberg-text-dim py-8 font-mono">
                  No loans found
                </TableCell>
              </TableRow>
            ) : (
              loans.map((loan) => (
                <TableRow
                  key={loan.loan_id}
                  onClick={() => handleLoanClick(loan)}
                  className={`${type === 'loans' ? 'cursor-pointer' : ''} hover:bg-bloomberg-surface/80 hover:border-bloomberg-orange/50 transition-colors border-b border-bloomberg-border group`}
                >
                  <TableCell className="font-mono text-sm text-bloomberg-text">
                    {loan.loan_id}
                  </TableCell>
                  <TableCell className="text-bloomberg-text font-mono">{loan.borrower_name}</TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className="text-xs bg-bloomberg-surface border-bloomberg-orange/50 text-bloomberg-orange font-mono"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {loan.product_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-bold text-bloomberg-green bloomberg-glow-green font-mono tabular-nums">
                    ${(loan.current_balance / 1e6).toFixed(2)}M
                  </TableCell>
                  <TableCell className="text-right text-bloomberg-amber font-mono tabular-nums">
                    {loan.interest_rate.toFixed(2)}%
                  </TableCell>
                  <TableCell>
                    <Badge className={`${getStatusColor(loan.payment_status)} font-mono text-xs`}>
                      {loan.payment_status}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-bloomberg-text-dim font-mono">
                    {new Date(loan.origination_date).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    {type === 'loans' && (
                      <ChevronRight className="h-4 w-4 text-bloomberg-text-dim group-hover:text-bloomberg-orange transition-colors" />
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
