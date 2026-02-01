'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ComponentDecayMetrics {
  relationship_category: string
  closure_rate: number
  abgr: number
  compound_factor: number
  year_1_retention: number
  year_2_retention: number
  year_3_retention: number
}

interface CohortSurvival {
  cohort_quarter: string
  months_since_opening: number
  survival_rate: number
  relationship_category: string
}

interface RunoffForecast {
  relationship_category: string
  year: number
  beginning_balance: number
  projected_balance: number
  runoff_amount: number
  cumulative_runoff_pct: number
}

export default function VintageAnalysisDashboard() {
  const [decayMetrics, setDecayMetrics] = useState<ComponentDecayMetrics[]>([])
  const [survivalData, setSurvivalData] = useState<CohortSurvival[]>([])
  const [runoffForecasts, setRunoffForecasts] = useState<RunoffForecast[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [decayRes, survivalRes, runoffRes] = await Promise.all([
        fetch('/api/data/component-decay-metrics'),
        fetch('/api/data/cohort-survival'),
        fetch('/api/data/runoff-forecasts')
      ])

      const decayData = await decayRes.json()
      const survivalDataRes = await survivalRes.json()
      const runoffData = await runoffRes.json()

      if (decayData.success) setDecayMetrics(decayData.data)
      if (survivalDataRes.success) setSurvivalData(survivalDataRes.data)
      if (runoffData.success) setRunoffForecasts(runoffData.data)

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch vintage analysis data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-bloomberg-text-dim font-mono">Loading vintage analysis...</div>
  }

  // Transform survival data for Recharts
  const survivalChartData = survivalData.reduce((acc: any[], item) => {
    const existing = acc.find(d => d.months === item.months_since_opening)
    if (existing) {
      existing[item.relationship_category] = item.survival_rate * 100
    } else {
      acc.push({
        months: item.months_since_opening,
        [item.relationship_category]: item.survival_rate * 100
      })
    }
    return acc
  }, []).sort((a, b) => a.months - b.months)

  // Transform runoff forecasts for Recharts
  const runoffChartData = runoffForecasts.reduce((acc: any[], item) => {
    const existing = acc.find(d => d.year === `Year ${item.year}`)
    if (existing) {
      existing[item.relationship_category] = (item.projected_balance / 1e9)
    } else {
      acc.push({
        year: `Year ${item.year}`,
        [item.relationship_category]: (item.projected_balance / 1e9)
      })
    }
    return acc
  }, [])

  const relationshipColors = {
    Strategic: '#059669',
    Tactical: '#0891B2',
    Expendable: '#DC2626'
  }

  return (
    <div className="space-y-6">
      {/* Component Decay Metrics Cards */}
      <div className="grid grid-cols-3 gap-6">
        {decayMetrics.map((metric, index) => (
          <Card key={index} className="border-2 border-bloomberg-border bg-bloomberg-surface">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono tracking-wider" style={{ color: relationshipColors[metric.relationship_category as keyof typeof relationshipColors] }}>
                {metric.relationship_category.toUpperCase()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mb-1">CLOSURE RATE (λ)</div>
                  <div className="text-2xl font-bold text-bloomberg-text font-mono">
                    {(metric.closure_rate * 100).toFixed(2)}%
                  </div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mt-1">Annual account closure</div>
                </div>
                <div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mb-1">ABGR (g)</div>
                  <div className="text-2xl font-bold text-bloomberg-text font-mono">
                    {(metric.abgr * 100) >= 0 ? '+' : ''}{(metric.abgr * 100).toFixed(2)}%
                  </div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mt-1">Balance growth rate</div>
                </div>
                <div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mb-1">3-YEAR RUNOFF</div>
                  <div className="text-2xl font-bold font-mono" style={{ color: relationshipColors[metric.relationship_category as keyof typeof relationshipColors] }}>
                    {(100 - metric.year_3_retention * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                    ${((metric.year_3_retention - 1) * -10).toFixed(2)}B lost
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Cohort Survival Curves (Kaplan-Meier) */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            KAPLAN-MEIER SURVIVAL CURVES
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Account retention by relationship category over 36 months</p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={survivalChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="months"
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Months Since Opening', position: 'insideBottom', offset: -5, fill: '#999', fontFamily: 'monospace' }}
              />
              <YAxis
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Survival Rate (%)', angle: -90, position: 'insideLeft', fill: '#999', fontFamily: 'monospace' }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '2px solid #ff8c00', fontFamily: 'monospace', fontSize: '12px' }}
                labelStyle={{ color: '#ff8c00' }}
              />
              <Legend
                wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
              <Line
                type="monotone"
                dataKey="Strategic"
                stroke={relationshipColors.Strategic}
                strokeWidth={3}
                dot={false}
                name="Strategic"
              />
              <Line
                type="monotone"
                dataKey="Tactical"
                stroke={relationshipColors.Tactical}
                strokeWidth={3}
                dot={false}
                name="Tactical"
              />
              <Line
                type="monotone"
                dataKey="Expendable"
                stroke={relationshipColors.Expendable}
                strokeWidth={3}
                dot={false}
                name="Expendable"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* 3-Year Runoff Forecasts */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            3-YEAR DEPOSIT RUNOFF PROJECTIONS
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Projected deposit balances by segment (D(t+1) = D(t) × (1-λ) × (1+g))</p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={runoffChartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="year"
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
              />
              <YAxis
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Balance ($B)', angle: -90, position: 'insideLeft', fill: '#999', fontFamily: 'monospace' }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '2px solid #ff8c00', fontFamily: 'monospace', fontSize: '12px' }}
                labelStyle={{ color: '#ff8c00' }}
                formatter={(value: any) => `$${value.toFixed(2)}B`}
              />
              <Legend
                wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
              <Bar dataKey="Strategic" fill={relationshipColors.Strategic} name="Strategic" />
              <Bar dataKey="Tactical" fill={relationshipColors.Tactical} name="Tactical" />
              <Bar dataKey="Expendable" fill={relationshipColors.Expendable} name="Expendable" />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Detailed Runoff Table */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            PHASE 2 RUNOFF FORECAST DETAILS
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Component decay model output by segment and year</p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono">
              <thead>
                <tr className="border-b-2 border-bloomberg-border">
                  <th className="text-left p-3 text-bloomberg-orange">SEGMENT</th>
                  <th className="text-right p-3 text-bloomberg-orange">YEAR</th>
                  <th className="text-right p-3 text-bloomberg-orange">BEGIN BAL</th>
                  <th className="text-right p-3 text-bloomberg-orange">END BAL</th>
                  <th className="text-right p-3 text-bloomberg-orange">RUNOFF $</th>
                  <th className="text-right p-3 text-bloomberg-orange">CUM %</th>
                </tr>
              </thead>
              <tbody>
                {runoffForecasts.map((forecast, index) => (
                  <tr key={index} className="border-b border-bloomberg-border hover:bg-black/20">
                    <td className="p-3" style={{ color: relationshipColors[forecast.relationship_category as keyof typeof relationshipColors] }}>
                      {forecast.relationship_category}
                    </td>
                    <td className="text-right p-3 text-bloomberg-text">{forecast.year}</td>
                    <td className="text-right p-3 text-bloomberg-text">
                      ${(forecast.beginning_balance / 1e9).toFixed(2)}B
                    </td>
                    <td className="text-right p-3 text-bloomberg-text">
                      ${(forecast.projected_balance / 1e9).toFixed(2)}B
                    </td>
                    <td className="text-right p-3 text-bloomberg-red">
                      -${(Math.abs(forecast.runoff_amount) / 1e9).toFixed(2)}B
                    </td>
                    <td className="text-right p-3 text-bloomberg-red font-bold">
                      {forecast.cumulative_runoff_pct.toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Chen Component Decay Formula */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            CHEN COMPONENT DECAY MODEL
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Separates closure rate from balance growth</p>
        </CardHeader>
        <CardContent>
          <div className="p-6 bg-black/40 border-2 border-bloomberg-orange/30 rounded">
            <div className="text-center mb-6">
              <div className="text-2xl font-bold text-bloomberg-orange font-mono">
                D(t+1) = D(t) × (1 - λ) × (1 + g)
              </div>
            </div>
            <div className="grid grid-cols-3 gap-6 text-sm font-mono">
              <div className="text-center">
                <div className="text-bloomberg-text-dim mb-2">D(t)</div>
                <div className="text-bloomberg-text">Deposits at time t</div>
              </div>
              <div className="text-center">
                <div className="text-bloomberg-text-dim mb-2">λ (lambda)</div>
                <div className="text-bloomberg-text">Account closure rate</div>
              </div>
              <div className="text-center">
                <div className="text-bloomberg-text-dim mb-2">g (ABGR)</div>
                <div className="text-bloomberg-text">Balance growth rate</div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
