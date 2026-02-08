'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { apiFetch } from '@/lib/api'

interface PpnrRow {
  month: string
  net_interest_income: number
  non_interest_income: number
  non_interest_expense: number
  ppnr: number
}

function toNumber(v: unknown): number {
  if (v === null || v === undefined) return 0
  const n = typeof v === 'number' ? v : Number(v)
  return Number.isFinite(n) ? n : 0
}

export default function PpnrDashboard() {
  const [rows, setRows] = useState<PpnrRow[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const res = await apiFetch('/api/data/ppnr-forecasts?limit=24')
        const json = await res.json()
        if (json?.success) {
          const normalized: PpnrRow[] = (json.data || []).map((r: any) => ({
            month: String(r.month),
            net_interest_income: toNumber(r.net_interest_income),
            non_interest_income: toNumber(r.non_interest_income),
            non_interest_expense: toNumber(r.non_interest_expense),
            ppnr: toNumber(r.ppnr),
          }))
          setRows(normalized)
        }
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  if (loading) {
    return <div className="text-sm text-bloomberg-text-dim font-mono">Loading PPNR forecasts...</div>
  }

  const latest = rows.length ? rows[rows.length - 1] : null

  const fmt = (v: number) => `$${(v / 1e6).toFixed(0)}M`

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-6">
        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">PPNR (LATEST)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-green font-mono bloomberg-glow-green">
              {latest ? fmt(latest.ppnr) : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Monthly forecast</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NET INTEREST INCOME</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-text font-mono">{latest ? fmt(latest.net_interest_income) : '—'}</div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Placeholder in demo</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NON-INTEREST INCOME</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-orange font-mono bloomberg-glow">
              {latest ? fmt(latest.non_interest_income) : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Fee income forecast</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NON-INTEREST EXPENSE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-red font-mono">
              {latest ? fmt(latest.non_interest_expense) : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Operating expense forecast</p>
          </CardContent>
        </Card>
      </div>

      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            PPNR PROJECTION
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Monthly forecast series (latest 24 periods)</p>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="month" stroke="#999" hide />
                <YAxis stroke="#999" tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                <Tooltip formatter={(v: any) => fmt(toNumber(v))} />
                <Legend />
                <Line type="monotone" dataKey="ppnr" name="PPNR" stroke="#10B981" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            COMPONENTS
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Income vs expense drivers</p>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis dataKey="month" stroke="#999" hide />
                <YAxis stroke="#999" tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                <Tooltip formatter={(v: any) => fmt(toNumber(v))} />
                <Legend />
                <Bar dataKey="non_interest_income" name="Non-Interest Income" fill="#FF8C00" />
                <Bar dataKey="non_interest_expense" name="Non-Interest Expense" fill="#FF3621" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

