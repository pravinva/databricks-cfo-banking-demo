'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { AlertTriangle } from 'lucide-react'
import { apiFetch } from '@/lib/api'
import { InsightTooltip, InsightValue } from '@/components/ui/insight-tooltip'

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

interface RepricingOpportunity {
  account_id: string
  product_type: string
  current_balance: number
  stated_rate: number
  market_rate: number
  generous_spread: number
  predicted_beta: number
  relationship_category: string
  recommended_cut_bps: number
  annual_income_uplift_usd: number
}

export default function DepositBetaDashboard() {
  const [metrics, setMetrics] = useState<BetaMetrics | null>(null)
  const [distribution, setDistribution] = useState<BetaDistribution[]>([])
  const [atRiskAccounts, setAtRiskAccounts] = useState<AtRiskAccount[]>([])
  const [repricingOpportunities, setRepricingOpportunities] = useState<RepricingOpportunity[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [metricsRes, distributionRes, atRiskRes, repricingRes] = await Promise.all([
        apiFetch('/api/data/deposit-beta-metrics'),
        apiFetch('/api/data/deposit-beta-distribution'),
        apiFetch('/api/data/at-risk-deposits'),
        apiFetch('/api/data/repricing-opportunities')
      ])

      const metricsData = await metricsRes.json()
      const distributionData = await distributionRes.json()
      const atRiskData = await atRiskRes.json()
      const repricingData = await repricingRes.json()

      if (metricsData.success) setMetrics(metricsData.data)
      if (distributionData.success) setDistribution(distributionData.data)
      if (atRiskData.success) setAtRiskAccounts(atRiskData.data)
      if (repricingData.success) setRepricingOpportunities(repricingData.data)

      if (!metricsData.success && !distributionData.success && !atRiskData.success && !repricingData.success) {
        setLoadError(
          metricsData.error ||
          distributionData.error ||
          atRiskData.error ||
          repricingData.error ||
          'Failed to load deposit beta data'
        )
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
            <InsightValue
              value={metrics ? metrics.avg_beta.toFixed(3) : '—'}
              title="Portfolio beta takeaway"
              text="Deposit beta estimates pass-through from market rates to offered rates. Lower beta implies stickier, lower-cost funding."
              valueClassName="text-3xl font-bold text-bloomberg-text font-mono"
            />
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
            <InsightValue
              value={metrics ? `$${(metrics.at_risk_balance / 1e9).toFixed(1)}B` : '—'}
              title="At-risk deposits takeaway"
              text="This is balance likely to reprice or run off first if competitors offer materially better rates."
              valueClassName="text-3xl font-bold text-bloomberg-orange font-mono bloomberg-glow"
            />
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
            <InsightValue
              value={metrics ? `${metrics.strategic_pct.toFixed(1)}%` : '—'}
              title="Strategic segment takeaway"
              text="Higher strategic share indicates a larger base of low-beta accounts and stronger funding durability."
              valueClassName="text-3xl font-bold text-bloomberg-green font-mono bloomberg-glow-green"
            />
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
            <InsightValue
              value={metrics ? `${metrics.expendable_pct.toFixed(1)}%` : '—'}
              title="Expendable segment takeaway"
              text="Higher expendable share signals more flight-prone balances and greater sensitivity under stress."
              valueClassName="text-3xl font-bold text-bloomberg-red font-mono bloomberg-glow-red"
            />
            <p className="text-xs text-bloomberg-text-dim font-mono mt-2">
              High sensitivity (hot money)
            </p>
            <p className="text-xs text-bloomberg-red font-mono font-bold">
              ⚠ Flight risk
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Priority layout: repricing opportunities get primary space */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-6">
        {/* Repricing Opportunities (Prominent) */}
        <Card className="xl:col-span-8 border-2 border-bloomberg-green/60 bg-bloomberg-surface shadow-sm">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-bloomberg-green tracking-wider font-mono">
              TOP 10 LOW-RISK REPRICING OPPORTUNITIES
            </CardTitle>
            <p className="text-xs text-bloomberg-text-dim font-mono">
              Generous-rate accounts where terms can be tightened with lower expected runoff risk
            </p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-[560px] overflow-y-auto">
              {repricingOpportunities.slice(0, 10).map((account, index) => (
                <div
                  key={index}
                  className="p-3 border border-bloomberg-border rounded-lg bg-slate-50 hover:border-bloomberg-green/70 transition-colors"
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
                      <div className="text-xs text-bloomberg-green font-mono font-bold mt-1">
                        +${(account.annual_income_uplift_usd / 1e3).toFixed(0)}K/yr
                      </div>
                    </div>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-xs font-mono">
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
                      <span className="text-bloomberg-text-dim">Cut:</span>
                      <br />
                      <span className="text-bloomberg-green font-bold">
                        {account.recommended_cut_bps.toFixed(0)} bps
                      </span>
                    </div>
                    <div>
                      <span className="text-bloomberg-text-dim">Beta:</span>
                      <br />
                      <span className="text-bloomberg-green font-bold">
                        {account.predicted_beta.toFixed(3)}
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

        {/* Compact beta distribution tile */}
        <Card className="xl:col-span-4 border-2 border-bloomberg-border bg-bloomberg-surface">
          <CardHeader>
            <CardTitle className="text-base font-bold text-bloomberg-orange tracking-wider font-mono">
              BETA DISTRIBUTION BY PRODUCT
            </CardTitle>
            <p className="text-xs text-bloomberg-text-dim font-mono">Compact product sensitivity tile</p>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {distribution.slice(0, 6).map((item, index) => (
                <div key={index} className="p-2 border border-bloomberg-border rounded bg-slate-50">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="font-bold text-bloomberg-orange">{item.product_type}</span>
                    <span className="text-bloomberg-text">{item.avg_beta.toFixed(3)}</span>
                  </div>
                  <div className="h-1.5 rounded-full mt-2 bg-slate-200">
                    <div
                      className="h-1.5 rounded-full"
                      style={{
                        width: `${(item.avg_beta / 1.0) * 100}%`,
                        backgroundColor: relationshipColors[item.relationship_category as keyof typeof relationshipColors] || '#666',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* At-Risk Accounts (secondary) */}
      <Card className="border-2 border-bloomberg-border bg-bloomberg-surface">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-bloomberg-orange tracking-wider font-mono">
            TOP 10 AT-RISK ACCOUNTS
          </CardTitle>
          <p className="text-xs text-bloomberg-text-dim font-mono">Accounts priced below market</p>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 max-h-[320px] overflow-y-auto">
            {atRiskAccounts.slice(0, 10).map((account, index) => (
              <div
                key={index}
                className="p-3 border border-bloomberg-border rounded-lg bg-slate-50 hover:border-bloomberg-red/70 transition-colors"
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
                      <span className="inline-flex items-center gap-1">
                        ${(account.current_balance / 1e6).toFixed(2)}M
                        <InsightTooltip
                          title="Account balance takeaway"
                          text="Larger at-risk balances have outsized impact on repricing cost and runoff sensitivity."
                        />
                      </span>
                    </div>
                    <div className="text-xs text-bloomberg-red font-mono font-bold mt-1">
                      <span className="inline-flex items-center gap-1">
                        β = {account.predicted_beta.toFixed(3)}
                        <InsightTooltip
                          title="Predicted beta takeaway"
                          text="Higher account beta indicates faster rate pass-through and greater likelihood of needing competitive repricing."
                        />
                      </span>
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
            <div className="p-4 border border-bloomberg-border rounded-lg bg-slate-50">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">MAPE (ENHANCED)</div>
              <div className="text-2xl font-bold text-bloomberg-green font-mono bloomberg-glow-green">
                <span className="inline-flex items-center gap-1">
                  7.2%
                  <InsightTooltip
                    title="MAPE takeaway"
                    text="Lower MAPE means better beta prediction accuracy and more reliable pricing decisions."
                  />
                </span>
              </div>
              <div className="text-xs text-bloomberg-green font-mono font-bold mt-1">
                +41% improvement
              </div>
            </div>
            <div className="p-4 border border-bloomberg-border rounded-lg bg-slate-50">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">BASELINE MAPE</div>
              <div className="text-2xl font-bold text-bloomberg-text-dim font-mono">
                <span className="inline-flex items-center gap-1">
                  12.3%
                  <InsightTooltip
                    title="Baseline MAPE takeaway"
                    text="This baseline error shows prior model quality; improvement vs this number indicates modeling gain."
                  />
                </span>
              </div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                15 features
              </div>
            </div>
            <div className="p-4 border border-bloomberg-border rounded-lg bg-slate-50">
              <div className="text-xs text-bloomberg-text-dim font-mono mb-2">FEATURES</div>
              <div className="text-2xl font-bold text-bloomberg-orange font-mono bloomberg-glow">
                <span className="inline-flex items-center gap-1">
                  19
                  <InsightTooltip
                    title="Feature set takeaway"
                    text="A broader feature set captures more behavioral drivers and usually improves segmentation precision."
                  />
                </span>
              </div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">
                Canonical scoring feature set
              </div>
            </div>
            <div className="p-4 border border-bloomberg-border rounded-lg bg-slate-50">
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
