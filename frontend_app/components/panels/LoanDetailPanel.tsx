'use client'

import { useState, useEffect } from 'react'
import { X, AlertCircle, FileText } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'

interface LoanDetail {
  loan_id: string
  borrower_name: string
  product_type: string
  current_balance: number
  original_amount: number
  interest_rate: number
  origination_date: string
  maturity_date: string
  payment_status: string
  days_past_due: number
  cecl_reserve: number
  pd: number
  lgd: number
  collateral_type: string
  collateral_value: number
  ltv_ratio: number
  officer_id: string
  branch_id: string
  gl_entries?: Array<any>
  subledger_entries?: Array<any>
}

interface Props {
  loanId: string
  open: boolean
  onClose: () => void
}

export default function LoanDetailPanel({ loanId, open, onClose }: Props) {
  const [loan, setLoan] = useState<LoanDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!open || !loanId) return

    setLoading(true)

    fetch(`http://localhost:8000/api/data/loan-detail/${loanId}`)
      .then(res => {
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`)
        }
        return res.json()
      })
      .then(data => {
        setLoan(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading loan:', err)
        setLoan(null)
        setLoading(false)
        onClose() // Close the dialog if fetch fails
      })
  }, [loanId, open])

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      'Current': 'bg-green-100 text-green-800 border-green-200',
      'Past_Due_30': 'bg-yellow-100 text-yellow-800 border-yellow-200',
      'Past_Due_60': 'bg-orange-100 text-orange-800 border-orange-200',
      'Past_Due_90': 'bg-red-100 text-red-800 border-red-200',
      'Default': 'bg-red-200 text-red-900 border-red-300'
    }
    return colors[status] || 'bg-slate-100 text-slate-800'
  }

  if (!loan && !loading) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl font-semibold flex items-center gap-3">
              <FileText className="h-6 w-6 text-blue-600" />
              Loan Detail: {loanId}
            </DialogTitle>
            <button
              onClick={onClose}
              className="text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-20 bg-slate-200 rounded" />
            <div className="h-40 bg-slate-200 rounded" />
          </div>
        ) : loan ? (
          <div className="space-y-6">
            {/* Summary Cards */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">CURRENT BALANCE</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">
                  ${((loan.current_balance || 0) / 1e6).toFixed(2)}M
                </p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">
                  Orig: ${((loan.original_amount || 0) / 1e6).toFixed(2)}M
                </p>
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">INTEREST RATE</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">
                  {(loan.interest_rate || 0).toFixed(2)}%
                </p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">
                  {loan.product_type}
                </p>
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">PAYMENT STATUS</p>
                <Badge className={getStatusColor(loan.payment_status)}>
                  {loan.payment_status}
                </Badge>
                {(loan.days_past_due || 0) > 0 && (
                  <p className="text-xs text-bloomberg-red mt-2 font-mono">
                    {loan.days_past_due} days past due
                  </p>
                )}
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">CECL RESERVE</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">
                  ${((loan.cecl_reserve || 0) / 1e3).toFixed(0)}K
                </p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">
                  {((loan.cecl_reserve || 0) / (loan.current_balance || 1) * 100).toFixed(2)}% of balance
                </p>
              </div>
            </div>

            {/* Detailed Tabs */}
            <Tabs defaultValue="overview" className="w-full">
              <TabsList className="grid grid-cols-4 w-full">
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="risk">Risk Profile</TabsTrigger>
                <TabsTrigger value="accounting">Accounting</TabsTrigger>
                <TabsTrigger value="history">History</TabsTrigger>
              </TabsList>

              <TabsContent value="overview" className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div>
                    <h3 className="font-semibold text-bloomberg-orange mb-3 font-mono">BORROWER INFORMATION</h3>
                    <dl className="space-y-2 text-sm bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Name:</dt>
                        <dd className="font-medium text-bloomberg-text">{loan.borrower_name}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Relationship Officer:</dt>
                        <dd className="font-medium font-mono text-bloomberg-text">{loan.officer_id}</dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Branch:</dt>
                        <dd className="font-medium font-mono text-bloomberg-text">{loan.branch_id}</dd>
                      </div>
                    </dl>
                  </div>

                  <div>
                    <h3 className="font-semibold text-bloomberg-orange mb-3 font-mono">LOAN TERMS</h3>
                    <dl className="space-y-2 text-sm bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Origination:</dt>
                        <dd className="font-medium text-bloomberg-text font-mono">
                          {new Date(loan.origination_date).toLocaleDateString()}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Maturity:</dt>
                        <dd className="font-medium text-bloomberg-text font-mono">
                          {new Date(loan.maturity_date).toLocaleDateString()}
                        </dd>
                      </div>
                      <div className="flex justify-between">
                        <dt className="text-bloomberg-text-dim">Original Amount:</dt>
                        <dd className="font-medium text-bloomberg-text font-mono">
                          ${(loan.original_amount / 1e6).toFixed(2)}M
                        </dd>
                      </div>
                    </dl>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold text-bloomberg-orange mb-3 font-mono">COLLATERAL</h3>
                  <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="text-sm text-bloomberg-text-dim">Type</p>
                        <p className="font-medium text-bloomberg-text">{loan.collateral_type}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-bloomberg-text-dim">Value</p>
                        <p className="font-medium text-bloomberg-text font-mono">
                          ${(loan.collateral_value / 1e6).toFixed(2)}M
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm text-bloomberg-text-dim">LTV Ratio</p>
                        <p className="font-medium text-bloomberg-text font-mono">
                          {(loan.ltv_ratio * 100).toFixed(1)}%
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="risk" className="space-y-4">
                <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-6">
                  <h3 className="font-semibold text-bloomberg-orange mb-4 flex items-center gap-2 font-mono">
                    <AlertCircle className="h-5 w-5 text-bloomberg-orange" />
                    CECL RISK PARAMETERS
                  </h3>

                  <div className="grid grid-cols-3 gap-6">
                    <div>
                      <p className="text-sm text-bloomberg-text-dim mb-2 font-mono">Probability of Default (PD)</p>
                      <div className="flex items-baseline gap-2">
                        <p className="text-3xl font-bold text-bloomberg-text font-mono">
                          {((loan.pd || 0) * 100).toFixed(2)}%
                        </p>
                      </div>
                      <div className="mt-2 h-2 bg-black/50 rounded-none overflow-hidden border border-bloomberg-orange/20">
                        <div
                          className="h-full bg-bloomberg-orange"
                          style={{ width: `${loan.pd * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-bloomberg-text-dim mb-2 font-mono">Loss Given Default (LGD)</p>
                      <div className="flex items-baseline gap-2">
                        <p className="text-3xl font-bold text-bloomberg-text font-mono">
                          {((loan.lgd || 0) * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="mt-2 h-2 bg-black/50 rounded-none overflow-hidden border border-bloomberg-orange/20">
                        <div
                          className="h-full bg-bloomberg-red"
                          style={{ width: `${loan.lgd * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <p className="text-sm text-bloomberg-text-dim mb-2 font-mono">CECL Reserve</p>
                      <div className="flex items-baseline gap-2">
                        <p className="text-3xl font-bold text-bloomberg-text font-mono">
                          ${((loan.cecl_reserve || 0) / 1e3).toFixed(0)}K
                        </p>
                      </div>
                      <p className="text-xs text-bloomberg-text-dim mt-2 font-mono">
                        {((loan.cecl_reserve || 0) / (loan.current_balance || 1) * 100).toFixed(3)}% of balance
                      </p>
                    </div>
                  </div>

                  <div className="mt-6 pt-4 border-t border-bloomberg-orange/30">
                    <p className="text-xs text-bloomberg-text-dim font-mono">
                      <strong className="text-bloomberg-orange">Formula:</strong> CECL Reserve = EAD × PD × LGD
                    </p>
                    <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">
                      = ${((loan.current_balance || 0) / 1e6).toFixed(2)}M × {((loan.pd || 0) * 100).toFixed(2)}% × {((loan.lgd || 0) * 100).toFixed(1)}%
                      = ${((loan.cecl_reserve || 0) / 1e3).toFixed(0)}K
                    </p>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="accounting" className="space-y-4">
                <h3 className="font-semibold text-bloomberg-text mb-3">GL Entries for This Loan</h3>

                {loan.gl_entries && loan.gl_entries.length > 0 ? (
                  <div className="space-y-2">
                    {loan.gl_entries.map((entry: any, index: number) => (
                      <div key={index} className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                        <div className="flex justify-between items-start mb-3">
                          <div>
                            <p className="font-mono text-sm font-medium text-bloomberg-orange">{entry.entry_id}</p>
                            <p className="text-xs text-bloomberg-text-dim">
                              {new Date(entry.entry_date).toLocaleDateString()}
                            </p>
                          </div>
                          <Badge variant={entry.is_balanced === 'true' || entry.is_balanced === true ? 'success' : 'destructive'}>
                            {entry.is_balanced === 'true' || entry.is_balanced === true ? 'Balanced' : 'Unbalanced'}
                          </Badge>
                        </div>

                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <p className="text-bloomberg-text-dim">Total Debits:</p>
                            <p className="font-medium text-bloomberg-text font-mono">
                              ${(entry.total_debits / 1e6).toFixed(2)}M
                            </p>
                          </div>
                          <div>
                            <p className="text-bloomberg-text-dim">Total Credits:</p>
                            <p className="font-medium text-bloomberg-text font-mono">
                              ${(entry.total_credits / 1e6).toFixed(2)}M
                            </p>
                          </div>
                        </div>

                        <p className="text-xs text-bloomberg-text-dim mt-3">{entry.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-bloomberg-text-dim">No GL entries found</p>
                )}

                <h3 className="font-semibold text-bloomberg-text mb-3 mt-6">Subledger Transactions</h3>

                {loan.subledger_entries && loan.subledger_entries.length > 0 ? (
                  <div className="border border-bloomberg-orange/30 rounded-none overflow-hidden bg-bloomberg-surface">
                    <table className="w-full text-sm">
                      <thead className="bg-black/50 border-b border-bloomberg-orange/30">
                        <tr>
                          <th className="text-left p-3 font-medium text-bloomberg-orange">Date</th>
                          <th className="text-left p-3 font-medium text-bloomberg-orange">Type</th>
                          <th className="text-right p-3 font-medium text-bloomberg-orange">Principal</th>
                          <th className="text-right p-3 font-medium text-bloomberg-orange">Interest</th>
                          <th className="text-right p-3 font-medium text-bloomberg-orange">Balance After</th>
                        </tr>
                      </thead>
                      <tbody>
                        {loan.subledger_entries.map((txn: any, index: number) => (
                          <tr key={index} className="border-t border-bloomberg-orange/10 hover:bg-bloomberg-orange/5">
                            <td className="p-3 text-bloomberg-text font-mono">
                              {new Date(txn.posting_date).toLocaleDateString()}
                            </td>
                            <td className="p-3">
                              <Badge variant="outline" className="text-xs">
                                {txn.transaction_type}
                              </Badge>
                            </td>
                            <td className="p-3 text-right font-mono text-bloomberg-text">
                              ${((txn.principal_amount || 0) / 1e3).toFixed(1)}K
                            </td>
                            <td className="p-3 text-right font-mono text-bloomberg-text">
                              ${((txn.interest_amount || 0) / 1e3).toFixed(1)}K
                            </td>
                            <td className="p-3 text-right font-mono font-medium text-bloomberg-text">
                              ${((txn.balance_after || 0) / 1e6).toFixed(2)}M
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <p className="text-sm text-bloomberg-text-dim">No subledger entries found</p>
                )}
              </TabsContent>

              <TabsContent value="history" className="space-y-4">
                <h3 className="font-semibold text-bloomberg-text mb-4">Payment History Timeline</h3>

                {loan.subledger_entries && loan.subledger_entries.length > 0 ? (
                  <div className="space-y-6">
                    {/* Balance Over Time Chart */}
                    <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                      <h4 className="text-sm font-semibold text-bloomberg-orange mb-4 font-mono">BALANCE TREND</h4>
                      <div className="space-y-2">
                        {loan.subledger_entries
                          .sort((a: any, b: any) => new Date(a.posting_date).getTime() - new Date(b.posting_date).getTime())
                          .map((txn: any, index: number) => {
                            const balancePercent = (txn.balance_after / loan.original_amount) * 100
                            return (
                              <div key={index} className="flex items-center gap-4">
                                <div className="w-32 text-xs text-bloomberg-text-dim font-mono">
                                  {new Date(txn.posting_date).toLocaleDateString()}
                                </div>
                                <div className="flex-1">
                                  <div className="h-8 bg-black/50 rounded-none overflow-hidden border border-bloomberg-orange/20">
                                    <div
                                      className="h-full bg-gradient-to-r from-bloomberg-orange to-bloomberg-orange/60 transition-all duration-300"
                                      style={{ width: `${balancePercent}%` }}
                                    />
                                  </div>
                                </div>
                                <div className="w-32 text-right">
                                  <p className="text-sm font-mono font-semibold text-bloomberg-text">
                                    ${(txn.balance_after / 1e6).toFixed(2)}M
                                  </p>
                                  <p className="text-xs text-bloomberg-text-dim">
                                    {balancePercent.toFixed(1)}%
                                  </p>
                                </div>
                              </div>
                            )
                          })}
                      </div>
                    </div>

                    {/* Payment Details Timeline */}
                    <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                      <h4 className="text-sm font-semibold text-bloomberg-orange mb-4 font-mono">TRANSACTION DETAILS</h4>
                      <div className="space-y-3">
                        {loan.subledger_entries
                          .sort((a: any, b: any) => new Date(b.posting_date).getTime() - new Date(a.posting_date).getTime())
                          .map((txn: any, index: number) => (
                            <div key={index} className="border-l-2 border-bloomberg-orange/50 pl-4 py-2 hover:border-bloomberg-orange transition-colors">
                              <div className="flex justify-between items-start mb-2">
                                <div>
                                  <p className="text-sm font-semibold text-bloomberg-text">
                                    {txn.transaction_type}
                                  </p>
                                  <p className="text-xs text-bloomberg-text-dim font-mono">
                                    {new Date(txn.posting_date).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'short',
                                      day: 'numeric'
                                    })}
                                  </p>
                                </div>
                                <Badge
                                  variant={txn.transaction_type === 'Origination' ? 'default' : 'outline'}
                                  className="text-xs"
                                >
                                  {txn.transaction_type}
                                </Badge>
                              </div>

                              <div className="grid grid-cols-3 gap-4 mt-2">
                                <div>
                                  <p className="text-xs text-bloomberg-text-dim">Principal</p>
                                  <p className="text-sm font-mono text-bloomberg-text">
                                    ${((txn.principal_amount || 0) / 1e3).toFixed(1)}K
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-bloomberg-text-dim">Interest</p>
                                  <p className="text-sm font-mono text-bloomberg-text">
                                    ${((txn.interest_amount || 0) / 1e3).toFixed(1)}K
                                  </p>
                                </div>
                                <div>
                                  <p className="text-xs text-bloomberg-text-dim">Balance After</p>
                                  <p className="text-sm font-mono font-semibold text-bloomberg-orange">
                                    ${((txn.balance_after || 0) / 1e6).toFixed(2)}M
                                  </p>
                                </div>
                              </div>
                            </div>
                          ))}
                      </div>
                    </div>

                    {/* Summary Stats */}
                    <div className="grid grid-cols-3 gap-4">
                      <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                        <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">TOTAL PRINCIPAL PAID</p>
                        <p className="text-2xl font-bold text-bloomberg-text font-mono">
                          ${(loan.subledger_entries
                            .filter((t: any) => t.transaction_type === 'Payment')
                            .reduce((sum: number, t: any) => sum + (t.principal_amount || 0), 0) / 1e6).toFixed(2)}M
                        </p>
                      </div>
                      <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                        <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">TOTAL INTEREST PAID</p>
                        <p className="text-2xl font-bold text-bloomberg-text font-mono">
                          ${(loan.subledger_entries
                            .filter((t: any) => t.transaction_type === 'Payment')
                            .reduce((sum: number, t: any) => sum + (t.interest_amount || 0), 0) / 1e3).toFixed(1)}K
                        </p>
                      </div>
                      <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                        <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">REMAINING BALANCE</p>
                        <p className="text-2xl font-bold text-bloomberg-orange font-mono">
                          ${(loan.current_balance / 1e6).toFixed(2)}M
                        </p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-bloomberg-text-dim">No payment history available</p>
                )}
              </TabsContent>
            </Tabs>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
