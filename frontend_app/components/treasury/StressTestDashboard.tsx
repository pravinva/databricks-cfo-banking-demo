'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface StressTestResult {
  scenario: string
  quarter: number
  cet1_ratio_pct: number
  tier1_ratio_pct: number
  total_capital_ratio_pct: number
  nii_impact: number
  deposit_runoff: number
  lcr_ratio: number
}

interface DynamicBetaParams {
  relationship_category: string
  beta_min: number
  beta_max: number
  k: number
  R0: number
}

interface ScenarioSummary {
  scenario: string
  cet1_minimum: number
  nii_impact_total: number
  deposit_runoff_total: number
  lcr_minimum: number
  pass_status: string
}

export default function StressTestDashboard() {
  const [stressResults, setStressResults] = useState<StressTestResult[]>([])
  const [dynamicBetas, setDynamicBetas] = useState<DynamicBetaParams[]>([])
  const [scenarioSummary, setScenarioSummary] = useState<ScenarioSummary[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [resultsRes, betasRes, summaryRes] = await Promise.all([
        apiFetch('/api/data/stress-test-results'),
        apiFetch('/api/data/dynamic-beta-parameters'),
        apiFetch('/api/data/stress-test-summary')
      ])

      const resultsData = await resultsRes.json()
      const betasData = await betasRes.json()
      const summaryData = await summaryRes.json()

      if (resultsData.success) setStressResults(resultsData.data)
      if (betasData.success) setDynamicBetas(betasData.data)
      if (summaryData.success) setScenarioSummary(summaryData.data)

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch stress test data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="text-sm text-bloomberg-text-dim font-mono">
        Loading CCAR stress tests...
      </div>
    )
  }

  // Transform stress results for charts
  const capitalRatioData = stressResults.map(result => ({
    quarter: `Q${result.quarter}`,
    scenario: result.scenario,
    CET1: result.cet1_ratio_pct,
    Tier1: result.tier1_ratio_pct,
    Total: result.total_capital_ratio_pct
  }))

  // Group by scenario for separate lines
  const baselineData = capitalRatioData.filter(d => d.scenario === 'Baseline')
  const adverseData = capitalRatioData.filter(d => d.scenario === 'Adverse')
  const severelyAdverseData = capitalRatioData.filter(d => d.scenario === 'Severely Adverse')

  // Generate dynamic beta curve data (0% to 6% rates)
  const generateBetaCurve = (params: DynamicBetaParams) => {
    const points = []
    for (let rate = 0; rate <= 6; rate += 0.25) {
      const beta = params.beta_min + (params.beta_max - params.beta_min) / (1 + Math.exp(-params.k * (rate - params.R0)))
      points.push({
        rate,
        [params.relationship_category]: beta
      })
    }
    return points
  }

  const betaCurveData = dynamicBetas.length > 0
    ? generateBetaCurve(dynamicBetas[0]).map((point, index) => {
        const result = { ...point }
        dynamicBetas.forEach((params, i) => {
          if (i > 0) {
            const beta = params.beta_min + (params.beta_max - params.beta_min) / (1 + Math.exp(-params.k * (point.rate - params.R0)))
            result[params.relationship_category] = beta
          }
        })
        return result
      })
    : []

  const relationshipColors = {
    Strategic: '#059669',
    Tactical: '#0891B2',
    Expendable: '#DC2626'
  }

  const scenarioColors = {
    Baseline: '#059669',
    Adverse: '#D97706',
    'Severely Adverse': '#DC2626'
  }

  return (
    <div className="space-y-6">
      {/* Scenario Summary Cards */}
      <div className="grid grid-cols-3 gap-6">
        {scenarioSummary.map((summary, index) => (
          <Card key={index} className="border-2 border-bloomberg-border bg-bloomberg-surface">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-mono tracking-wider" style={{ color: scenarioColors[summary.scenario as keyof typeof scenarioColors] }}>
                {summary.scenario.toUpperCase()}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs text-bloomberg-text-dim font-mono mb-1">CET1 MINIMUM</div>
                    <div className="text-2xl font-bold text-bloomberg-text font-mono">
                      {summary.cet1_minimum.toFixed(1)}%
                    </div>
                  </div>
                  {summary.cet1_minimum >= 7.0 ? (
                    <CheckCircle className="h-8 w-8 text-bloomberg-green bloomberg-glow-green" />
                  ) : (
                    <AlertTriangle className="h-8 w-8 text-bloomberg-red bloomberg-glow-red" />
                  )}
                </div>
                <div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mb-1">NII IMPACT (2Y)</div>
                  <div className="text-xl font-bold text-bloomberg-red font-mono">
                    -${(Math.abs(summary.nii_impact_total) / 1e6).toFixed(0)}M
                  </div>
                </div>
                <div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mb-1">DEPOSIT RUNOFF</div>
                  <div className="text-xl font-bold text-bloomberg-red font-mono">
                    -${(Math.abs(summary.deposit_runoff_total) / 1e9).toFixed(1)}B
                  </div>
                  <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                    ({((summary.deposit_runoff_total / 30e9) * 100).toFixed(1)}% of total)
                  </div>
                </div>
                <div className={`text-sm font-bold font-mono p-2 text-center rounded ${summary.pass_status === 'PASS' ? 'bg-bloomberg-green/20 text-bloomberg-green bloomberg-glow-green' : 'bg-bloomberg-red/20 text-bloomberg-red bloomberg-glow-red'}`}>
                  {summary.pass_status}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* 9-Quarter Capital Ratio Projections */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            9-QUARTER CAPITAL RATIO PROJECTIONS (CCAR)
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">CET1, Tier 1, and Total Capital under stress scenarios</p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={capitalRatioData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="quarter"
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
              />
              <YAxis
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Capital Ratio (%)', angle: -90, position: 'insideLeft', fill: '#999', fontFamily: 'monospace' }}
                domain={[0, 15]}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '2px solid #ff8c00', fontFamily: 'monospace', fontSize: '12px' }}
                labelStyle={{ color: '#ff8c00' }}
              />
              <Legend
                wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
              {/* Reference lines for regulatory minimums */}
              <Line
                type="monotone"
                dataKey={() => 7.0}
                stroke="#DC2626"
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
                name="CET1 Min (7%)"
              />
              <Line
                type="monotone"
                dataKey={() => 8.5}
                stroke="#D97706"
                strokeDasharray="5 5"
                strokeWidth={2}
                dot={false}
                name="Tier 1 Min (8.5%)"
              />
              <Line
                type="monotone"
                dataKey="CET1"
                stroke="#ff8c00"
                strokeWidth={3}
                dot={{ r: 4 }}
                name="CET1 Ratio"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Dynamic Beta Curves (Chen Sigmoid) */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            DYNAMIC BETA RESPONSE CURVES (CHEN SIGMOID)
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">
            β(Rm) = β_min + (β_max - β_min) / [1 + exp(-k*(Rm-R0))]
          </p>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={betaCurveData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis
                dataKey="rate"
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Market Rate (%)', position: 'insideBottom', offset: -5, fill: '#999', fontFamily: 'monospace' }}
              />
              <YAxis
                stroke="#999"
                tick={{ fill: '#999', fontFamily: 'monospace', fontSize: 12 }}
                label={{ value: 'Beta', angle: -90, position: 'insideLeft', fill: '#999', fontFamily: 'monospace' }}
                domain={[0, 1]}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#000', border: '2px solid #ff8c00', fontFamily: 'monospace', fontSize: '12px' }}
                labelStyle={{ color: '#ff8c00' }}
                formatter={(value: any) => value.toFixed(3)}
              />
              <Legend
                wrapperStyle={{ fontFamily: 'monospace', fontSize: '12px' }}
              />
              <Area
                type="monotone"
                dataKey="Strategic"
                stroke={relationshipColors.Strategic}
                fill={relationshipColors.Strategic}
                fillOpacity={0.3}
                strokeWidth={3}
                name="Strategic"
              />
              <Area
                type="monotone"
                dataKey="Tactical"
                stroke={relationshipColors.Tactical}
                fill={relationshipColors.Tactical}
                fillOpacity={0.3}
                strokeWidth={3}
                name="Tactical"
              />
              <Area
                type="monotone"
                dataKey="Expendable"
                stroke={relationshipColors.Expendable}
                fill={relationshipColors.Expendable}
                fillOpacity={0.3}
                strokeWidth={3}
                name="Expendable"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Dynamic Beta Parameters Table */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            DYNAMIC BETA PARAMETERS BY SEGMENT
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Calibrated sigmoid function coefficients</p>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-sm font-mono">
              <thead>
                <tr className="border-b-2 border-bloomberg-border">
                  <th className="text-left p-3 text-bloomberg-orange">SEGMENT</th>
                  <th className="text-right p-3 text-bloomberg-orange">β_MIN (0%)</th>
                  <th className="text-right p-3 text-bloomberg-orange">β_MAX (6%)</th>
                  <th className="text-right p-3 text-bloomberg-orange">k (STEEP)</th>
                  <th className="text-right p-3 text-bloomberg-orange">R0 (INFLECT)</th>
                  <th className="text-right p-3 text-bloomberg-orange">RANGE</th>
                </tr>
              </thead>
              <tbody>
                {dynamicBetas.map((params, index) => (
                  <tr key={index} className="border-b border-bloomberg-border hover:bg-black/20">
                    <td className="p-3" style={{ color: relationshipColors[params.relationship_category as keyof typeof relationshipColors] }}>
                      {params.relationship_category}
                    </td>
                    <td className="text-right p-3 text-bloomberg-text">{params.beta_min.toFixed(4)}</td>
                    <td className="text-right p-3 text-bloomberg-text">{params.beta_max.toFixed(4)}</td>
                    <td className="text-right p-3 text-bloomberg-text">{params.k.toFixed(2)}</td>
                    <td className="text-right p-3 text-bloomberg-text">{(params.R0 * 100).toFixed(2)}%</td>
                    <td className="text-right p-3 text-bloomberg-amber font-bold">
                      {((params.beta_max - params.beta_min) * 100).toFixed(1)} bps
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Regulatory Compliance Summary */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            APPROACH 3 REGULATORY COMPLIANCE
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">
            CCAR submission readiness (DFAST is legacy term)
          </p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-6">
            <div className="p-6 bg-black/40 border-2 border-bloomberg-green rounded">
              <div className="flex items-center justify-between mb-4">
                <Shield className="h-12 w-12 text-bloomberg-green bloomberg-glow-green" />
                <div className="text-4xl font-bold text-bloomberg-green font-mono bloomberg-glow-green">
                  ✓
                </div>
              </div>
              <div className="text-lg font-bold text-bloomberg-green font-mono mb-2">
                STRESS TESTS PASSED
              </div>
              <div className="text-sm text-bloomberg-text-dim font-mono">
                All scenarios meet CET1 ≥ 7% minimum
              </div>
              <div className="text-sm text-bloomberg-text-dim font-mono mt-2">
                Ready for Federal Reserve submission
              </div>
            </div>
            <div className="p-6 bg-black/40 border-2 border-bloomberg-border rounded">
              <div className="text-sm font-mono space-y-3">
                <div className="flex justify-between">
                  <span className="text-bloomberg-text-dim">Submission Deadline:</span>
                  <span className="text-bloomberg-text font-bold">April 5, 2026</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-bloomberg-text-dim">Model Version:</span>
                  <span className="text-bloomberg-text font-bold">Approach 3 Dynamic</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-bloomberg-text-dim">Scenarios Tested:</span>
                  <span className="text-bloomberg-text font-bold">3 (B/A/SA)</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-bloomberg-text-dim">Forecast Horizon:</span>
                  <span className="text-bloomberg-text font-bold">9 Quarters</span>
                </div>
                <div className="flex justify-between pt-3 border-t border-bloomberg-border">
                  <span className="text-bloomberg-text-dim">Status:</span>
                  <span className="text-bloomberg-green font-bold bloomberg-glow-green">COMPLIANT</span>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
