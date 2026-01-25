'use client'

import { useState, useEffect } from 'react'
import { useDrillDown } from '@/lib/drill-down-context'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { ChevronRight, TrendingUp, DollarSign } from 'lucide-react'

interface PortfolioItem {
  product_type: string
  count: number
  balance_billions: number
  avg_rate: number
  reserve_pct?: number
}

interface PortfolioDetailTableProps {
  type: 'loans' | 'deposits'
}

export default function PortfolioDetailTable({ type }: PortfolioDetailTableProps) {
  const [data, setData] = useState<PortfolioItem[]>([])
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    fetchData()
  }, [type])

  const fetchData = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/data/portfolio-breakdown')
      const result = await res.json()
      if (result.success) {
        // Convert array data to objects
        const arrayData = type === 'loans' ? result.loans : result.deposits
        const items: PortfolioItem[] = arrayData.map((row: any[]) => ({
          product_type: row[0],
          count: parseInt(row[1]),
          balance_billions: parseFloat(row[2]),
          avg_rate: parseFloat(row[3]),
          reserve_pct: row[4] ? parseFloat(row[4]) : undefined
        }))
        setData(items)
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error)
      setLoading(false)
    }
  }

  const handleRowClick = (item: PortfolioItem) => {
    // Navigate to filtered loan/deposit table
    if (type === 'loans') {
      navigateTo('loan-table', { product_type: item.product_type }, `${item.product_type} Loans`)
    } else {
      navigateTo('deposit-table', { product_type: item.product_type }, `${item.product_type} Deposits`)
    }
  }

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-12 bg-bloomberg-surface rounded-none" />
        <div className="h-96 bg-bloomberg-surface rounded-none" />
      </div>
    )
  }

  const totalBalance = data.reduce((sum, item) => sum + item.balance_billions, 0)
  const totalCount = data.reduce((sum, item) => sum + item.count, 0)

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-bloomberg-surface border-2 border-bloomberg-border rounded-none p-6 hover:border-bloomberg-orange/50 transition-colors">
          <div className="flex items-center gap-2 text-bloomberg-text-dim mb-3">
            <DollarSign className="h-5 w-5" />
            <p className="text-xs font-mono font-bold tracking-wider uppercase">Total Balance</p>
          </div>
          <p className="text-3xl font-bold text-bloomberg-orange bloomberg-glow font-mono tabular-nums">
            ${totalBalance.toFixed(2)}B
          </p>
        </div>

        <div className="bg-bloomberg-surface border-2 border-bloomberg-border rounded-none p-6 hover:border-bloomberg-orange/50 transition-colors">
          <div className="flex items-center gap-2 text-bloomberg-text-dim mb-3">
            <TrendingUp className="h-5 w-5" />
            <p className="text-xs font-mono font-bold tracking-wider uppercase">Total {type === 'loans' ? 'Loans' : 'Accounts'}</p>
          </div>
          <p className="text-3xl font-bold text-bloomberg-green bloomberg-glow-green font-mono tabular-nums">
            {totalCount.toLocaleString()}
          </p>
        </div>

        <div className="bg-bloomberg-surface border-2 border-bloomberg-border rounded-none p-6 hover:border-bloomberg-orange/50 transition-colors">
          <div className="flex items-center gap-2 text-bloomberg-text-dim mb-3">
            <TrendingUp className="h-5 w-5" />
            <p className="text-xs font-mono font-bold tracking-wider uppercase">Product Types</p>
          </div>
          <p className="text-3xl font-bold text-bloomberg-amber font-mono tabular-nums">
            {data.length}
          </p>
        </div>
      </div>

      {/* Portfolio Table */}
      <div className="border-2 border-bloomberg-border rounded-none overflow-hidden bg-bloomberg-surface shadow-xl">
        <div className="bg-bloomberg-surface px-6 py-4 border-b-2 border-bloomberg-orange/30">
          <h3 className="text-lg font-bold text-bloomberg-orange font-mono uppercase tracking-wider">
            {type === 'loans' ? 'Loan' : 'Deposit'} Portfolio Breakdown
          </h3>
          <p className="text-sm text-bloomberg-text-dim mt-1 font-mono">
            Click any row to view detailed {type} list
          </p>
        </div>

        <Table>
          <TableHeader>
            <TableRow className="bg-bloomberg-surface border-b-2 border-bloomberg-orange/30">
              <TableHead className="text-bloomberg-orange font-mono font-bold">Product Type</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Count</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Balance</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Avg Rate</TableHead>
              {type === 'loans' && <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Reserve %</TableHead>}
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">% of Total</TableHead>
              <TableHead></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((item, index) => {
              const percentOfTotal = (item.balance_billions / totalBalance) * 100

              return (
                <TableRow
                  key={index}
                  onClick={() => handleRowClick(item)}
                  className="cursor-pointer hover:bg-bloomberg-surface/80 hover:border-bloomberg-orange/50 transition-colors border-b border-bloomberg-border group"
                >
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-xs bg-bloomberg-surface border-bloomberg-orange/50 text-bloomberg-orange font-mono">
                        {item.product_type}
                      </Badge>
                    </div>
                  </TableCell>
                  <TableCell className="text-right font-bold text-bloomberg-text font-mono tabular-nums">
                    {item.count.toLocaleString()}
                  </TableCell>
                  <TableCell className="text-right font-bold text-bloomberg-green bloomberg-glow-green font-mono tabular-nums">
                    ${item.balance_billions.toFixed(2)}B
                  </TableCell>
                  <TableCell className="text-right text-bloomberg-amber font-mono tabular-nums">
                    {item.avg_rate.toFixed(2)}%
                  </TableCell>
                  {type === 'loans' && (
                    <TableCell className="text-right">
                      <Badge className="bg-bloomberg-surface border-2 border-bloomberg-amber text-bloomberg-amber font-mono">
                        {item.reserve_pct?.toFixed(2)}%
                      </Badge>
                    </TableCell>
                  )}
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <div className="w-16 h-2 bg-bloomberg-border rounded-none overflow-hidden">
                        <div
                          className="h-full bg-bloomberg-orange rounded-none"
                          style={{ width: `${percentOfTotal}%` }}
                        />
                      </div>
                      <span className="text-sm text-bloomberg-text-dim font-mono tabular-nums w-12">
                        {percentOfTotal.toFixed(1)}%
                      </span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <ChevronRight className="h-4 w-4 text-bloomberg-text-dim group-hover:text-bloomberg-orange transition-colors" />
                  </TableCell>
                </TableRow>
              )
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
