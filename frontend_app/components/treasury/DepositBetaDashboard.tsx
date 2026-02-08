'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, AlertTriangle, Info } from 'lucide-react'
import { apiFetch } from '@/lib/api'

interface BetaMetrics {
  total_accounts: number
  total_balance: number
  avg_beta: number
  at_risk_accounts: number
  at_risk_balance: number
  strategic_pct: number
  tactical_pct: number
  expendable_pct: number
}

interface BetaDistribution {
  product_type: string
  account_count: number
  total_balance: number
  avg_beta: number
  relationship_category: string
}

interface AtRiskAccount {
  account_id: string
  product_type: string
  current_balance: number
  stated_rate: number
  market_rate: number
  rate_gap: number
  predicted_beta: number
  relationship_category: string
}

export default function DepositBetaDashboard() {
  const [metrics, setMetrics] = useState<BetaMetrics | null>(null)
  const [distribution, setDistribution] = useState<BetaDistribution[]>([])
  const [atRiskAccounts, setAtRiskAccounts] = useState<AtRiskAccount[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [metricsRes, distributionRes, atRiskRes] = await Promise.all([
        apiFetch('/api/data/deposit-beta-metrics'),
        apiFetch('/api/data/deposit-beta-distribution'),
        apiFetch('/api/data/at-risk-deposits')
      ])

      const metricsData = await metricsRes.json()
      const distributionData = await distributionRes.json()
      const atRiskData = await atRiskRes.json()

      if (metricsData.success) setMetrics(metricsData.data)
      if (distributionData.success) setDistribution(distributionData.data)
      if (atRiskData.success) setAtRiskAccounts(atRiskData.data)

      if (!metricsData.success && !distributionData.success && !atRiskData.success) {
        setLoadError(metricsData.error || distributionData.error || atRiskData.error || 'Failed to load deposit beta data')
      } else {
        setLoadError(null)
      }

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch deposit beta data:', error)
      setLoadError('Failed to fetch deposit beta data')
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-bloomberg-text-dim font-mono">Loading deposit beta model...</div>
  }

  const relationshipColors = {
    'Low Beta': '#059669',     // Green
    'Medium Beta': '#F59E0B',  // Amber
    'High Beta': '#DC2626'     // Red
  }

  return (
    <div className="space-y-6">
      {loadError && (
        <div className="border-2 border-bloomberg-red bg-bloomberg-surface p-4 font-mono text-sm text-bloomberg-red">
          {loadError}
        </div>
      )}

      {/* KPI Cards Row */}
      <div className="grid grid-cols-4 gap-6">
        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">PORTFOLIO BETA</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-text font-mono">
              {metrics ? metrics.avg_beta.toFixed(3) : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">
              {metrics ? `${metrics.total_accounts.toLocaleString()} accounts` : '—'}
            </p>
            <p className="text-xs text-bloomberg-text-dim font-mono">
              {metrics ? `$${(metrics.total_balance / 1e9).toFixed(1)}B total` : '—'}
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-orange bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider flex items-center">
              AT-RISK DEPOSITS
              <AlertTriangle className="h-4 w-4 ml-2 text-bloomberg-orange bloomberg-glow" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-orange font-mono bloomberg-glow">
              {metrics ? `$${(metrics.at_risk_balance / 1e9).toFixed(1)}B` : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">
              {metrics ? `${metrics.at_risk_accounts.toLocaleString()} accounts` : '—'}
            </p>
            <p className="text-xs text-bloomberg-amber font-mono font-bold">
              Below market rate
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">STRATEGIC</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-green font-mono bloomberg-glow-green">
              {metrics ? `${metrics.strategic_pct.toFixed(1)}%` : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">
              Low sensitivity (sticky)
            </p>
            <p className="text-xs text-bloomberg-green font-mono font-bold">
              ✓ Stable funding
            </p>
          </CardContent>
        </Card>

        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-mono text-bloomberg-text-dim tracking-wider">EXPENDABLE</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-bloomberg-red font-mono bloomberg-glow-red">
              {metrics ? `${metrics.expendable_pct.toFixed(1)}%` : '—'}
            </div>
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">
              High sensitivity (hot money)
            </p>
            <p className="text-xs text-bloomberg-red font-mono font-bold">
              ⚠ Flight risk
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Beta Distribution by Product & Relationship */}
      <div className="grid grid-cols-2 gap-6">
        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
              BETA DISTRIBUTION BY PRODUCT
            </CardTitle>
            <p className="text-xs text-bloomberg-text-dim font-mono">Rate sensitivity by deposit type</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {distribution.map((item, index) => (
                <div
                  key={index}
                  className="p-4 border-2 border-bloomberg-border bg-black/20 hover:border-bloomberg-orange/70 transition-colors"
                >
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <div className="font-bold text-bloomberg-orange font-mono text-sm">{item.product_type}</div>
                      <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                        {item.account_count.toLocaleString()} accounts
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-bloomberg-text font-mono text-xl">
                        {item.avg_beta.toFixed(3)}
                      </div>
                      <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                        ${(item.total_balance / 1e9).toFixed(2)}B
                      </div>
                    </div>
                  </div>
                  <div
                    className="h-2 rounded-full mt-2"
                    style={{
                      width: `${(item.avg_beta / 1.0) * 100}%`,
                      backgroundColor: relationshipColors[item.relationship_category as keyof typeof relationshipColors] || '#666'
                    }}
                  />
                  <div className="text-xs font-mono mt-2" style={{ color: relationshipColors[item.relationship_category as keyof typeof relationshipColors] }}>
                    {item.relationship_category}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* At-Risk Accounts Table */}
        <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader>
            <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
              TOP 10 AT-RISK ACCOUNTS
            </CardTitle>
            <p className="text-xs text-bloomberg-text-dim font-mono">Accounts priced below market</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[500px] overflow-y-auto">
              {atRiskAccounts.slice(0, 10).map((account, index) => (
                <div
                  key={index}
                  className="p-3 border-2 border-bloomberg-border bg-black/20 hover:border-bloomberg-red/70 transition-colors"
                >
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-bold text-bloomberg-text font-mono text-xs">
                        {account.account_id}
                      </div>
                      <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                        {account.product_type}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-bloomberg-text font-mono text-sm">
                        ${(account.current_balance / 1e6).toFixed(2)}M
                      </div>
                      <div className="text-xs text-bloomberg-red font-mono font-bold mt-1">
                        β = {account.predicted_beta.toFixed(3)}
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                    <div>
                      <span className="text-bloomberg-text-dim">Our Rate:</span>
                      <br />
                      <span className="text-bloomberg-text">{(account.stated_rate * 100).toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-bloomberg-text-dim">Market:</span>
                      <br />
                      <span className="text-bloomberg-text">{(account.market_rate * 100).toFixed(2)}%</span>
                    </div>
                    <div>
                      <span className="text-bloomberg-text-dim">Gap:</span>
                      <br />
                      <span className="text-bloomberg-red font-bold">
                        {(account.rate_gap * 100).toFixed(0)} bps
                      </span>
                    </div>
                  </div>
                  <div
                    className="text-xs font-mono font-bold mt-2"
                    style={{ color: relationshipColors[account.relationship_category as keyof typeof relationshipColors] }}
                  >
                    {account.relationship_category}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Model Performance Metrics */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            APPROACH 1 MODEL PERFORMANCE
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Static beta model with 19 features</p>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-6">
            <div className="p-4 border-2 border-bloomberg-border bg-black/20">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">MAPE (ENHANCED)</div>
              <div className="text-2xl font-bold text-bloomberg-green font-mono bloomberg-glow-green">
                7.2%
              </div>
              <div className="text-xs text-bloomberg-green font-mono font-bold mt-1">
                +41% improvement
              </div>
            </div>
            <div className="p-4 border-2 border-bloomberg-border bg-black/20">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">BASELINE MAPE</div>
              <div className="text-2xl font-bold text-bloomberg-text-dim font-mono">
                12.3%
              </div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                15 features
              </div>
            </div>
            <div className="p-4 border-2 border-bloomberg-border bg-black/20">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">FEATURES</div>
              <div className="text-2xl font-bold text-bloomberg-orange font-mono bloomberg-glow">
                19
              </div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                Canonical scoring feature set
              </div>
            </div>
            <div className="p-4 border-2 border-bloomberg-border bg-black/20">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">MODEL VERSION</div>
              <div className="text-2xl font-bold text-bloomberg-text font-mono">
                @champion
              </div>
              <div className="text-xs text-bloomberg-green font-mono font-bold mt-1">
                ✓ Production
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
