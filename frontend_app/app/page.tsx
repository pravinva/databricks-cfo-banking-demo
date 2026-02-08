'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Activity, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import YieldCurveChart from '@/components/charts/YieldCurveChart'
import MetricCard from '@/components/MetricCard'
import { DrillDownProvider, useDrillDown } from '@/lib/drill-down-context'
import Breadcrumbs from '@/components/Breadcrumbs'
import DepositTable from '@/components/tables/DepositTable'
import DepositDetailPanel from '@/components/panels/DepositDetailPanel'
import DepositBetaDashboard from '@/components/treasury/DepositBetaDashboard'
import VintageAnalysisDashboard from '@/components/treasury/VintageAnalysisDashboard'
import StressTestDashboard from '@/components/treasury/StressTestDashboard'
import PpnrDashboard from '@/components/treasury/PpnrDashboard'
import { apiFetch } from '@/lib/api'

function DataSourceTooltip({ source }: { source: string }) {
  return (
    <div className="group relative inline-block ml-2">
      <Info className="h-4 w-4 text-slate-400 cursor-help" />
      <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-50 w-64">
        <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg">
          <div className="font-medium mb-1">Data Source</div>
          <div className="text-slate-300">{source}</div>
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1">
            <div className="border-4 border-transparent border-t-slate-900"></div>
          </div>
        </div>
      </div>
    </div>
  )
}

function DepositPortfolioBreakdown() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const res = await apiFetch('/api/data/portfolio-breakdown')
      const result = await res.json()
      if (result.success) {
        setData(result.deposits || [])
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch portfolio data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-600">Loading...</div>
  }

  return (
    <div className="space-y-3">
      {data.map((item: any, index: number) => (
        <div
          key={index}
          onClick={() => navigateTo('deposit-table', { product_type: item[0] }, `${item[0]} Deposits`)}
          className="flex items-center justify-between p-4 border-2 border-bloomberg-border bg-bloomberg-surface hover:border-bloomberg-orange/70 transition-colors group cursor-pointer"
        >
          <div>
            <div className="font-bold text-bloomberg-orange group-hover:text-bloomberg-amber transition-colors font-mono text-sm">{item[0]}</div>
            <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{Number(item[1]).toLocaleString()} accounts</div>
          </div>
          <div className="text-right">
            <div className="font-bold text-bloomberg-text font-mono text-lg">${Number(item[2]).toFixed(2)}B</div>
            <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{Number(item[3]).toFixed(2)}% avg rate</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function DashboardContent() {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [depositBetaMetrics, setDepositBetaMetrics] = useState<any>(null)
  const [ppnrLatest, setPpnrLatest] = useState<any>(null)
  const [currentTime, setCurrentTime] = useState<string>('')
  const [selectedDepositAccountId, setSelectedDepositAccountId] = useState<string | null>(null)
  const { state, navigateTo } = useDrillDown()

  useEffect(() => {
    // Set initial time on client only
    setCurrentTime(new Date().toLocaleTimeString())

    // Update time every second
    const timeInterval = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString())
    }, 1000)

    return () => clearInterval(timeInterval)
  }, [])

  useEffect(() => {
    fetchSummary()
    const interval = setInterval(fetchSummary, 60000) // Refresh every minute
    return () => clearInterval(interval)
  }, [])

  const fetchSummary = async () => {
    try {
      const res = await apiFetch('/api/data/summary')
      const data = await res.json()
      setSummary(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch summary:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    const fetchTreasuryKpis = async () => {
      try {
        const [betaRes, ppnrRes] = await Promise.all([
          apiFetch('/api/data/deposit-beta-metrics'),
          apiFetch('/api/data/ppnr-forecasts'),
        ])

        const betaJson = await betaRes.json()
        if (betaJson?.success) setDepositBetaMetrics(betaJson.data)

        const ppnrJson = await ppnrRes.json()
        if (ppnrJson?.success && Array.isArray(ppnrJson?.data) && ppnrJson.data.length > 0) {
          setPpnrLatest(ppnrJson.data[ppnrJson.data.length - 1])
        }
      } catch (e) {
        // KPI cards should fail soft (dashboard tabs still render)
        console.warn('Failed to fetch treasury KPIs:', e)
      }
    }

    fetchTreasuryKpis()
  }, [])

  return (
    <div className="min-h-screen bg-bloomberg-bg">
      {/* Header - Bloomberg Terminal Style */}
      <header className="bloomberg-header sticky top-0 z-50">
        <div className="container mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-bloomberg-orange bloomberg-glow tracking-wide">
                TREASURY MODELING COMMAND CENTER
              </h1>
              <p className="text-xs text-bloomberg-text-dim font-mono mt-1">
                DEPOSITS + PPNR | POWERED BY DATABRICKS LAKEHOUSE
              </p>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-3 text-xs font-mono text-bloomberg-text-dim">
                <span>{currentTime || '--:--:--'}</span>
                <div className="h-2 w-2 rounded-full bg-bloomberg-green animate-pulse bloomberg-glow-green" />
                <span className="text-bloomberg-green font-bold">LIVE</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">
        <Breadcrumbs />

        {state.view === 'deposit-table' ? (
          <DepositTable
            filters={state.filters}
            onAccountClick={(accountId) => setSelectedDepositAccountId(accountId)}
          />
        ) : (
          <>
            {/* KPI Cards Row */}
            <div className="grid grid-cols-3 gap-6 mb-8">
              <div onClick={() => navigateTo('deposit-table', {}, 'All Deposits')} className="cursor-pointer">
                <MetricCard
                  title="Total Deposits"
                  value={summary?.success ? `$${(summary.deposits / 1e9).toFixed(1)}B` : 'Loading...'}
                  change="+1.8%"
                  trend="up"
                  icon={<Activity className="h-5 w-5" />}
                  dataSource="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE account_status = 'Active' (SUM current_balance) → agent_tools.get_portfolio_summary()"
                />
              </div>
              <MetricCard
                title="Avg Predicted Beta"
                value={
                  depositBetaMetrics && typeof depositBetaMetrics?.avg_beta === 'number'
                    ? depositBetaMetrics.avg_beta.toFixed(3)
                    : '—'
                }
                change="Approach 1"
                trend="up"
                icon={<TrendingUp className="h-5 w-5" />}
                dataSource="Unity Catalog: cfo_banking_demo.ml_models.deposit_beta_predictions (AVG predicted_beta) → /api/data/deposit-beta-metrics"
              />
              <MetricCard
                title="Latest PPNR"
                value={ppnrLatest?.ppnr != null ? `$${(Number(ppnrLatest.ppnr) / 1e9).toFixed(2)}B` : '—'}
                change="Monthly forecast"
                trend="up"
                icon={<TrendingUp className="h-5 w-5" />}
                dataSource="Unity Catalog: cfo_banking_demo.ml_models.ppnr_forecasts (latest month) → /api/data/ppnr-forecasts"
              />
            </div>

            {/* Treasury Modeling Tabs */}
            <Tabs defaultValue="deposits" className="space-y-6 mb-8">
              <TabsList>
                <TabsTrigger value="deposits">Deposits</TabsTrigger>
                <TabsTrigger value="deposit-beta" className="text-bloomberg-orange">
                  Deposit Beta
                </TabsTrigger>
                <TabsTrigger value="vintage" className="text-bloomberg-orange">
                  Vintage Analysis
                </TabsTrigger>
                <TabsTrigger value="stress-test" className="text-bloomberg-orange">
                  CCAR/DFAST
                </TabsTrigger>
                <TabsTrigger value="ppnr" className="text-bloomberg-orange">
                  PPNR
                </TabsTrigger>
              </TabsList>

              <TabsContent value="deposits" className="space-y-6">
                <Card>
                  <CardHeader>
                    <div className="flex items-center">
                      <CardTitle>Deposit Portfolio by Product</CardTitle>
                      <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts → Aggregated by product_type with current_balance and stated_rate" />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <DepositPortfolioBreakdown />
                  </CardContent>
                </Card>
              </TabsContent>

              <TabsContent value="deposit-beta" className="space-y-6">
                <DepositBetaDashboard />
              </TabsContent>

              <TabsContent value="vintage" className="space-y-6">
                <VintageAnalysisDashboard />
              </TabsContent>

              <TabsContent value="stress-test" className="space-y-6">
                <StressTestDashboard />
              </TabsContent>

              <TabsContent value="ppnr" className="space-y-6">
                <PpnrDashboard />
              </TabsContent>
            </Tabs>

            {/* Market Data (used by deposit + PPNR models) */}
            <div className="grid grid-cols-1 gap-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center">
                    <h3
                      className="text-lg font-bold leading-none tracking-wider font-mono uppercase"
                      style={{ color: '#ff8c00 !important' }}
                    >
                      US TREASURY YIELD CURVE
                    </h3>
                    <DataSourceTooltip source="Alpha Vantage API → agent_tools.get_current_treasury_yields() → U.S. Department of Treasury daily rates" />
                  </div>
                  <p className="text-sm font-mono" style={{ color: '#999999' }}>
                    Live market data
                  </p>
                </CardHeader>
                <CardContent>
                  <YieldCurveChart />
                </CardContent>
              </Card>
            </div>
          </>
        )}

        {selectedDepositAccountId && (
          <DepositDetailPanel
            accountId={selectedDepositAccountId}
            open={!!selectedDepositAccountId}
            onClose={() => setSelectedDepositAccountId(null)}
          />
        )}
      </main>
    </div>
  )
}

export default function Page() {
  return (
    <DrillDownProvider>
      <DashboardContent />
    </DrillDownProvider>
  )
}
