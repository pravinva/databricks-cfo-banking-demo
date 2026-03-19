'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { apiFetch } from '@/lib/api'
import { InsightTooltip, InsightValue } from '@/components/ui/insight-tooltip'

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
  const [scenarioRows, setScenarioRows] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const load = async () => {
      try {
        const [res, scenarioRes] = await Promise.all([
          apiFetch('/api/data/ppnr-forecasts?limit=24'),
          apiFetch('/api/data/ppnr-scenario-summary'),
        ])
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
        const scenarioJson = await scenarioRes.json()
        if (scenarioJson?.success && Array.isArray(scenarioJson?.data)) {
          setScenarioRows(scenarioJson.data)
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
  const netInterestIncomeColor = '#3B82F6'
  const nonInterestIncomeColor = '#2F9E8F'
  const nonInterestExpenseColor = '#C27A7A'

  const ppnrTakeaway = (value: number) =>
    value >= 0
      ? 'Positive PPNR indicates core earnings capacity before provisions and taxes.'
      : 'Negative PPNR indicates core operating loss before provisions and taxes.'

  const deltaTakeaway = (label: string, value: number) =>
    `${label} is ${value >= 0 ? 'supporting' : 'pressuring'} PPNR by ${value >= 0 ? '+' : '-'}$${Math.abs(value / 1e6).toFixed(0)}M vs baseline in Q9.`

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-6">
        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">PPNR (LATEST)</CardTitle>
          </CardHeader>
          <CardContent>
            <InsightValue
              value={latest ? fmt(latest.ppnr) : '—'}
              title="PPNR latest takeaway"
              text={ppnrTakeaway(toNumber(latest?.ppnr))}
              valueClassName="text-3xl font-bold text-bloomberg-green font-mono bloomberg-glow-green"
            />
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Monthly forecast</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NET INTEREST INCOME</CardTitle>
          </CardHeader>
          <CardContent>
            <InsightValue
              value={latest ? fmt(latest.net_interest_income) : '—'}
              title="Net interest income takeaway"
              text="NII reflects earnings from asset-liability spread; lower NII typically compresses PPNR."
              valueClassName="text-3xl font-bold text-bloomberg-text font-mono"
            />
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Placeholder in demo</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NON-INTEREST INCOME</CardTitle>
          </CardHeader>
          <CardContent>
            <InsightValue
              value={latest ? fmt(latest.non_interest_income) : '—'}
              title="Non-interest income takeaway"
              text="Higher fee and ancillary income provides a buffer against rate-cycle pressure."
              valueClassName="text-3xl font-bold text-bloomberg-orange font-mono bloomberg-glow"
            />
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">Fee income forecast</p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">NON-INTEREST EXPENSE</CardTitle>
          </CardHeader>
          <CardContent>
            <InsightValue
              value={latest ? fmt(latest.non_interest_expense) : '—'}
              title="Non-interest expense takeaway"
              text="Operating expense discipline is a direct lever for improving PPNR resilience."
              valueClassName="text-3xl font-bold text-bloomberg-red font-mono"
            />
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
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
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
          <p className="text-xs text-bloomberg-text-dim font-mono">NII, non-interest income, and non-interest expense drivers</p>
        </CardHeader>
        <CardContent>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rows}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#999" hide />
                <YAxis stroke="#999" tickFormatter={(v) => `${(v / 1e6).toFixed(0)}M`} />
                <Tooltip formatter={(v: any) => fmt(toNumber(v))} />
                <Legend />
                <Bar dataKey="net_interest_income" name="Net Interest Income" fill={netInterestIncomeColor} />
                <Bar dataKey="non_interest_income" name="Non-Interest Income" fill={nonInterestIncomeColor} />
                <Bar dataKey="non_interest_expense" name="Non-Interest Expense" fill={nonInterestExpenseColor} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            SCENARIO ATTRIBUTION (Q9)
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Rate + Market + Liquidity components</p>
        </CardHeader>
        <CardContent>
          {scenarioRows.length === 0 ? (
            <div className="text-xs text-bloomberg-text-dim font-mono">Run scenario planning notebooks to populate this section.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                    <th className="text-left py-2">Scenario</th>
                    <th className="text-right py-2">Q9 PPNR</th>
                    <th className="text-right py-2">Δ Rate</th>
                    <th className="text-right py-2">Δ Market</th>
                    <th className="text-right py-2">Δ Liquidity</th>
                  </tr>
                </thead>
                <tbody>
                  {scenarioRows.map((r, i) => (
                    <tr key={i} className="border-b border-bloomberg-border/40">
                      <td className="py-2 text-bloomberg-text">
                        <span className="inline-flex items-center">
                          {r.scenario}
                          <InsightTooltip
                            title="Scenario takeaway"
                            text={ppnrTakeaway(toNumber(r.q9_ppnr_usd))}
                            className="ml-2"
                          />
                        </span>
                      </td>
                      <td className="py-2 text-right text-bloomberg-text">
                        <span className="inline-flex items-center justify-end gap-1">
                          ${(toNumber(r.q9_ppnr_usd) / 1e6).toFixed(0)}M
                          <InsightTooltip
                            title="Q9 PPNR interpretation"
                            text={ppnrTakeaway(toNumber(r.q9_ppnr_usd))}
                          />
                        </span>
                      </td>
                      <td className={`py-2 text-right ${toNumber(r.q9_delta_rate_usd) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                        <span className="inline-flex items-center justify-end gap-1">
                          {toNumber(r.q9_delta_rate_usd) >= 0 ? '+' : ''}${(toNumber(r.q9_delta_rate_usd) / 1e6).toFixed(0)}M
                          <InsightTooltip
                            title="Rate delta interpretation"
                            text={deltaTakeaway('Rate effect', toNumber(r.q9_delta_rate_usd))}
                          />
                        </span>
                      </td>
                      <td className={`py-2 text-right ${toNumber(r.q9_delta_market_usd) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                        <span className="inline-flex items-center justify-end gap-1">
                          {toNumber(r.q9_delta_market_usd) >= 0 ? '+' : ''}${(toNumber(r.q9_delta_market_usd) / 1e6).toFixed(0)}M
                          <InsightTooltip
                            title="Market delta interpretation"
                            text={deltaTakeaway('Market effect', toNumber(r.q9_delta_market_usd))}
                          />
                        </span>
                      </td>
                      <td className={`py-2 text-right ${toNumber(r.q9_delta_liquidity_usd) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                        <span className="inline-flex items-center justify-end gap-1">
                          {toNumber(r.q9_delta_liquidity_usd) >= 0 ? '+' : ''}${(toNumber(r.q9_delta_liquidity_usd) / 1e6).toFixed(0)}M
                          <InsightTooltip
                            title="Liquidity delta interpretation"
                            text={deltaTakeaway('Liquidity effect', toNumber(r.q9_delta_liquidity_usd))}
                          />
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

