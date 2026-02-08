'use client'

import { useEffect, useState } from 'react'
import { X, FileText } from 'lucide-react'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { apiFetch } from '@/lib/api'

interface GlEntry {
  entry_id: string
  source_transaction_id: string | null
  entry_date: string
  entry_timestamp: string
  total_debits: number
  total_credits: number
  is_balanced: boolean
  description: string
}

interface SubledgerTxn {
  transaction_id: string
  transaction_timestamp: string
  transaction_type: string
  amount: number
  balance_after: number
  gl_entry_id: string | null
  channel: string | null
  description: string | null
}

interface DepositDetail {
  account_id: string
  customer_name: string
  product_type: string
  customer_segment: string
  account_open_date: string | null
  current_balance: number
  stated_rate: number
  beta: number | null
  predicted_beta: number | null
  account_status: string
  gl_entries: GlEntry[]
  subledger_entries: SubledgerTxn[]
}

interface Props {
  accountId: string
  open: boolean
  onClose: () => void
}

export default function DepositDetailPanel({ accountId, open, onClose }: Props) {
  const [deposit, setDeposit] = useState<DepositDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!open || !accountId) return
    setLoading(true)

    apiFetch(`/api/data/deposit-detail/${encodeURIComponent(accountId)}`)
      .then(res => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`)
        return res.json()
      })
      .then(data => {
        setDeposit(data)
        setLoading(false)
      })
      .catch(err => {
        console.error('Error loading deposit detail:', err)
        setDeposit(null)
        setLoading(false)
        onClose()
      })
  }, [accountId, open])

  if (!deposit && !loading) return null

  const money = (v: number) => `$${(v / 1e6).toFixed(2)}M`

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center justify-between">
            <DialogTitle className="text-2xl font-semibold flex items-center gap-3">
              <FileText className="h-6 w-6 text-bloomberg-orange" />
              Deposit Detail: {accountId}
            </DialogTitle>
            <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>
        </DialogHeader>

        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="h-20 bg-slate-200 rounded" />
            <div className="h-40 bg-slate-200 rounded" />
          </div>
        ) : deposit ? (
          <div className="space-y-6">
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">CURRENT BALANCE</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">{money(deposit.current_balance || 0)}</p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">{deposit.product_type}</p>
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">STATED RATE</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">
                  {(Number(deposit.stated_rate || 0) * 100).toFixed(2)}%
                </p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">{deposit.account_status}</p>
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">PREDICTED BETA</p>
                <p className="text-2xl font-bold text-bloomberg-text font-mono">
                  {deposit.predicted_beta != null ? Number(deposit.predicted_beta).toFixed(3) : '—'}
                </p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">
                  Base beta: {deposit.beta != null ? Number(deposit.beta).toFixed(3) : '—'}
                </p>
              </div>

              <div className="bg-bloomberg-surface border border-bloomberg-orange/30 rounded-none p-4">
                <p className="text-xs text-bloomberg-text-dim mb-1 font-mono">CUSTOMER</p>
                <p className="text-lg font-bold text-bloomberg-text font-mono truncate">{deposit.customer_name}</p>
                <p className="text-xs text-bloomberg-text-dim mt-1 font-mono">{deposit.customer_segment}</p>
              </div>
            </div>

            <Tabs defaultValue="subledger" className="space-y-4">
              <TabsList>
                <TabsTrigger value="subledger">Subledger</TabsTrigger>
                <TabsTrigger value="gl">GL Entries</TabsTrigger>
              </TabsList>

              <TabsContent value="subledger" className="space-y-3">
                <div className="space-y-2 max-h-[420px] overflow-y-auto">
                  {deposit.subledger_entries?.length ? (
                    deposit.subledger_entries.map((t, idx) => (
                      <div key={idx} className="p-3 border-2 border-bloomberg-border bg-black/20 hover:border-bloomberg-orange/60 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="font-mono text-xs text-bloomberg-text">{t.transaction_id}</div>
                          <Badge variant="outline" className="bg-bloomberg-surface border-bloomberg-orange/50 text-bloomberg-orange font-mono">
                            {t.transaction_type}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-2 text-xs font-mono text-bloomberg-text-dim">
                          <div>
                            <div className="text-bloomberg-text-dim">Amount</div>
                            <div className="text-bloomberg-text">{money(Number(t.amount || 0))}</div>
                          </div>
                          <div>
                            <div className="text-bloomberg-text-dim">Balance After</div>
                            <div className="text-bloomberg-text">{money(Number(t.balance_after || 0))}</div>
                          </div>
                          <div>
                            <div className="text-bloomberg-text-dim">Channel</div>
                            <div className="text-bloomberg-text">{t.channel || '—'}</div>
                          </div>
                        </div>
                        {t.description && <div className="text-xs text-bloomberg-text-dim font-mono mt-2">{t.description}</div>}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-bloomberg-text-dim font-mono">No subledger transactions found</p>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="gl" className="space-y-3">
                <div className="space-y-2 max-h-[420px] overflow-y-auto">
                  {deposit.gl_entries?.length ? (
                    deposit.gl_entries.map((e, idx) => (
                      <div key={idx} className="p-3 border-2 border-bloomberg-border bg-black/20 hover:border-bloomberg-orange/60 transition-colors">
                        <div className="flex items-center justify-between">
                          <div className="font-mono text-xs text-bloomberg-text">{e.entry_id}</div>
                          <Badge
                            variant="outline"
                            className={`font-mono ${
                              e.is_balanced
                                ? 'bg-bloomberg-surface border-bloomberg-green text-bloomberg-green'
                                : 'bg-bloomberg-surface border-bloomberg-red text-bloomberg-red'
                            }`}
                          >
                            {e.is_balanced ? 'BALANCED' : 'UNBALANCED'}
                          </Badge>
                        </div>
                        <div className="grid grid-cols-3 gap-3 mt-2 text-xs font-mono text-bloomberg-text-dim">
                          <div>
                            <div>Debits</div>
                            <div className="text-bloomberg-text">{money(Number(e.total_debits || 0))}</div>
                          </div>
                          <div>
                            <div>Credits</div>
                            <div className="text-bloomberg-text">{money(Number(e.total_credits || 0))}</div>
                          </div>
                          <div>
                            <div>Posted</div>
                            <div className="text-bloomberg-text">{String(e.entry_date || '').slice(0, 10) || '—'}</div>
                          </div>
                        </div>
                        {e.description && <div className="text-xs text-bloomberg-text-dim font-mono mt-2">{e.description}</div>}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-bloomberg-text-dim font-mono">No GL entries found</p>
                  )}
                </div>
              </TabsContent>
            </Tabs>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}

