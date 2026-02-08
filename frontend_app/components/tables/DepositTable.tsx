'use client'

import { useEffect, useState } from 'react'
import { Filter } from 'lucide-react'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { apiFetch } from '@/lib/api'

interface DepositRow {
  account_id: string
  customer_name: string
  product_type: string
  customer_segment: string
  current_balance: number
  stated_rate: number
  beta: number
  account_status: string
  account_open_date?: string
}

interface Props {
  filters?: Record<string, any>
  onAccountClick?: (accountId: string) => void
}

export default function DepositTable({ filters = {}, onAccountClick }: Props) {
  const [rows, setRows] = useState<DepositRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true)
        const qp = new URLSearchParams()
        if (filters.product_type) qp.set('product_type', String(filters.product_type))
        if (filters.customer_segment) qp.set('customer_segment', String(filters.customer_segment))
        qp.set('limit', String(filters.limit || 200))

        // Query directly from UC for deposit rows (avoid legacy loan-shaped deposits payload)
        const res = await apiFetch(`/api/data/deposit-accounts?${qp.toString()}`)
        const json = await res.json()
        if (json?.success) setRows(json.data || [])
      } catch (e) {
        console.error('Failed to load deposits:', e)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [filters.product_type, filters.customer_segment, filters.limit])

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
      <div className="flex items-center justify-between bg-bloomberg-surface rounded-none border-2 border-bloomberg-border p-4 hover:border-bloomberg-orange/50 transition-colors">
        <div className="flex items-center gap-2 text-sm text-bloomberg-text-dim">
          <Filter className="h-4 w-4" />
          <span className="font-bold font-mono">{rows.length.toLocaleString()} DEPOSITS</span>
          {filters.product_type && (
            <Badge variant="outline" className="bg-bloomberg-surface border-bloomberg-orange text-bloomberg-orange font-mono">
              {filters.product_type}
            </Badge>
          )}
        </div>
      </div>

      <div className="border-2 border-bloomberg-border rounded-none overflow-hidden bg-bloomberg-surface shadow-xl">
        <Table>
          <TableHeader>
            <TableRow className="bg-bloomberg-surface border-b-2 border-bloomberg-orange/30">
              <TableHead className="text-bloomberg-orange font-mono font-bold">Account ID</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Customer</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Product</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Balance</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Rate</TableHead>
              <TableHead className="text-right text-bloomberg-orange font-mono font-bold">Beta</TableHead>
              <TableHead className="text-bloomberg-orange font-mono font-bold">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} className="text-center text-bloomberg-text-dim py-8 font-mono">
                  No deposits found
                </TableCell>
              </TableRow>
            ) : (
              rows.map((r) => (
                <TableRow
                  key={r.account_id}
                  onClick={() => onAccountClick?.(r.account_id)}
                  className="cursor-pointer hover:bg-bloomberg-surface/80 hover:border-bloomberg-orange/50 transition-colors border-b border-bloomberg-border group"
                >
                  <TableCell className="font-mono text-xs text-bloomberg-text">{r.account_id}</TableCell>
                  <TableCell className="text-bloomberg-text font-mono">{r.customer_name}</TableCell>
                  <TableCell>
                    <Badge variant="outline" className="text-xs bg-bloomberg-surface border-bloomberg-orange/50 text-bloomberg-orange font-mono">
                      {r.product_type}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right font-bold text-bloomberg-green bloomberg-glow-green font-mono tabular-nums">
                    ${(Number(r.current_balance || 0) / 1e6).toFixed(2)}M
                  </TableCell>
                  <TableCell className="text-right text-bloomberg-amber font-mono tabular-nums">
                    {(Number(r.stated_rate || 0) * 100).toFixed(2)}%
                  </TableCell>
                  <TableCell className="text-right text-bloomberg-text font-mono tabular-nums">
                    {Number(r.beta || 0).toFixed(3)}
                  </TableCell>
                  <TableCell className="text-bloomberg-text-dim font-mono">{r.account_status}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}

