'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, Shield, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import YieldCurveChart from '@/components/charts/YieldCurveChart'
import LiquidityWaterfall from '@/components/charts/LiquidityWaterfall'
import MetricCard from '@/components/MetricCard'
import Link from 'next/link'
import { DrillDownProvider, useDrillDown } from '@/lib/drill-down-context'
import Breadcrumbs from '@/components/Breadcrumbs'
import LoanTable from '@/components/tables/LoanTable'
import LoanDetailPanel from '@/components/panels/LoanDetailPanel'
import PortfolioDetailTable from '@/components/tables/PortfolioDetailTable'

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

function PortfolioBreakdown({ type }: { type: 'loans' | 'deposits' }) {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    fetchData()
  }, [type])

  const fetchData = async () => {
    try {
      const res = await fetch('/api/data/portfolio-breakdown')
      const result = await res.json()
      if (result.success) {
        setData(type === 'loans' ? result.loans : result.deposits)
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
          onClick={() => {
            // Navigate to appropriate table filtered by product type
            const productType = item[0]
            const view = type === 'loans' ? 'loan-table' : 'deposit-table'
            navigateTo(view, { product_type: productType }, `${productType} ${type === 'loans' ? 'Loans' : 'Deposits'}`)
          }}
          className="flex items-center justify-between p-4 border-2 border-bloomberg-border bg-bloomberg-surface hover:border-bloomberg-orange/70 transition-colors cursor-pointer group"
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

function RiskMetrics() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const res = await fetch('/api/data/risk-metrics')
      const result = await res.json()
      if (result.success) {
        setData(result)
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch risk metrics:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-600">Loading risk metrics...</div>
  }

  if (!data) {
    return <div className="text-sm text-slate-600">No risk data available</div>
  }

  return (
    <div className="grid grid-cols-2 gap-6">
      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900">Credit Risk by Product</h3>
        <div className="space-y-3">
          {data.credit_risk?.map((item: any, index: number) => (
            <div
              key={index}
              onClick={() => {
                // Navigate to loan table filtered by product type
                navigateTo('loan-table', { product_type: item[0] }, `${item[0]} Loans - Risk View`)
              }}
              className="p-4 border-2 border-bloomberg-border bg-bloomberg-surface hover:border-bloomberg-orange/70 transition-colors cursor-pointer group"
            >
              <div className="flex justify-between items-start mb-3">
                <div className="font-bold text-bloomberg-orange group-hover:text-bloomberg-amber transition-colors font-mono text-sm">{item[0]}</div>
                <div className="text-lg font-bold text-bloomberg-text font-mono">${Number(item[1]).toFixed(2)}B</div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-bloomberg-text-dim font-mono">
                <div>NPL: <span className="text-bloomberg-red font-bold">{Number(item[2]).toFixed(2)}%</span></div>
                <div>RSV: <span className="text-bloomberg-amber">${Number(item[3]).toFixed(2)}B</span></div>
                <div className="col-span-2">Ratio: <span className="text-bloomberg-text">{Number(item[4]).toFixed(2)}%</span></div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900">Rate Shock Stress (100 bps)</h3>
        <div className="space-y-3">
          {data.rate_shock_stress?.map((item: any, index: number) => (
            <div key={index} className="p-4 border-2 border-bloomberg-border bg-bloomberg-surface">
              <div className="flex justify-between items-start mb-3">
                <div className="font-bold text-bloomberg-orange font-mono text-sm">{item.product}</div>
                <div className="text-sm text-bloomberg-red font-bold font-mono bloomberg-glow-red">
                  -${(item.runoff_100bps / 1e6).toFixed(1)}M
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-bloomberg-text-dim font-mono">
                <div>BETA: <span className="text-bloomberg-text">{item.beta.toFixed(4)}</span></div>
                <div>RUN: <span className="text-bloomberg-red">{item.runoff_pct.toFixed(2)}%</span></div>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-bloomberg-surface border-2 border-bloomberg-border mt-4">
          <h4 className="font-bold text-bloomberg-orange mb-3 font-mono text-sm tracking-wider">LCR STRESS TEST</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-bloomberg-text-dim font-mono mb-1">BASE CASE</div>
              <div className="font-bold text-bloomberg-text font-mono text-lg">
                {data.lcr_stress?.base.ratio.toFixed(2)}%
              </div>
              <div className={`text-xs font-bold font-mono mt-1 ${data.lcr_stress?.base.status === 'Pass' ? 'text-bloomberg-green bloomberg-glow-green' : 'text-bloomberg-red bloomberg-glow-red'}`}>
                {data.lcr_stress?.base.status}
              </div>
            </div>
            <div>
              <div className="text-xs text-bloomberg-text-dim font-mono mb-1">1.5X STRESS</div>
              <div className="font-bold text-bloomberg-text font-mono text-lg">
                {data.lcr_stress?.stressed.ratio.toFixed(2)}%
              </div>
              <div className={`text-xs font-bold font-mono mt-1 ${data.lcr_stress?.stressed.status === 'Pass' ? 'text-bloomberg-green bloomberg-glow-green' : 'text-bloomberg-red bloomberg-glow-red'}`}>
                {data.lcr_stress?.stressed.status}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function RecentActivity() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const { navigateTo } = useDrillDown()

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const res = await fetch('/api/data/recent-activity')
      const result = await res.json()
      if (result.success) {
        setData(result.activities || [])
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch activity:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-sm text-slate-600">Loading recent activity...</div>
  }

  return (
    <div className="space-y-3">
      {data.map((item: any, index: number) => (
        <div
          key={index}
          onClick={() => {
            // Navigate to loan table filtered by product type
            navigateTo('loan-table', { product_type: item[1] }, `${item[1]} Loans`)
          }}
          className="flex items-center justify-between p-4 border-2 border-bloomberg-border bg-bloomberg-surface hover:border-bloomberg-orange/70 transition-colors cursor-pointer group"
        >
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <div className="font-bold text-bloomberg-orange group-hover:text-bloomberg-amber transition-colors font-mono text-sm">{item[0]}</div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{item[1]}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-bold text-bloomberg-text font-mono text-lg">${(Number(item[2]) / 1000).toFixed(1)}K</div>
            <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{new Date(item[3]).toLocaleDateString()}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function DashboardContent() {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedLoan, setSelectedLoan] = useState<string | null>(null)
  const [currentTime, setCurrentTime] = useState<string>('')
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
      const res = await fetch('/api/data/summary')
      const data = await res.json()
      setSummary(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch summary:', error)
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-bloomberg-bg">
      {/* Header - Bloomberg Terminal Style */}
      <header className="bloomberg-header sticky top-0 z-50">
        <div className="container mx-auto px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-bloomberg-orange bloomberg-glow tracking-wide">
                BANK CFO COMMAND CENTER
              </h1>
              <p className="text-xs text-bloomberg-text-dim font-mono mt-1">
                POWERED BY DATABRICKS LAKEHOUSE | REAL-TIME ANALYTICS
              </p>
            </div>

            <div className="flex items-center gap-6">
              <Link
                href="/assistant"
                className="text-sm font-bold text-bloomberg-amber hover:text-bloomberg-orange transition-colors tracking-wide"
              >
                AI ASSISTANT →
              </Link>
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

        {/* Breadcrumbs */}
        <Breadcrumbs />

        {/* Conditional View Rendering */}
        {state.view === 'loan-table' ? (
          <LoanTable
            type="loans"
            filters={state.filters}
            onLoanClick={(loanId) => setSelectedLoan(loanId)}
          />
        ) : state.view === 'deposit-table' ? (
          <LoanTable
            type="deposits"
            filters={state.filters}
            onLoanClick={(loanId) => setSelectedLoan(loanId)}
          />
        ) : state.view === 'portfolio-loans' ? (
          <PortfolioDetailTable type="loans" />
        ) : state.view === 'portfolio-deposits' ? (
          <PortfolioDetailTable type="deposits" />
        ) : (
          <>
            {/* KPI Cards Row */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <div onClick={() => navigateTo('loan-table', {}, 'All Loans')} className="cursor-pointer">
            <MetricCard
              title="Total Assets"
              value={summary?.success ? `$${(summary.total_assets / 1e9).toFixed(1)}B` : 'Loading...'}
              change="+2.1%"
              trend="up"
              icon={<TrendingUp className="h-5 w-5" />}
              dataSource="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio (SUM current_balance) + silver_finance.securities (SUM market_value) → agent_tools.get_portfolio_summary()"
            />
          </div>
          <div onClick={() => navigateTo('loan-table', {}, 'All Deposits')} className="cursor-pointer">
            <MetricCard
              title="Total Deposits"
              value={summary?.success ? `$${(summary.deposits / 1e9).toFixed(1)}B` : 'Loading...'}
              change="+1.8%"
              trend="up"
              icon={<Activity className="h-5 w-5" />}
              dataSource="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE account_status = 'Active' (SUM current_balance) → agent_tools.get_portfolio_summary()"
            />
          </div>
          <div onClick={() => navigateTo('loan-table', {}, 'All Loans')} className="cursor-pointer">
            <MetricCard
              title="Loans"
              value={summary?.success ? `$${(summary.loans / 1e9).toFixed(1)}B` : 'Loading...'}
              change="-12 bps"
              trend="down"
              icon={<TrendingDown className="h-5 w-5" />}
              dataSource="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true (SUM current_balance) → agent_tools.get_portfolio_summary()"
            />
          </div>
          <div onClick={() => navigateTo('loan-table', {}, 'All Securities')} className="cursor-pointer">
            <MetricCard
              title="Securities"
              value={summary?.success ? `$${(summary.securities / 1e9).toFixed(1)}B` : 'Loading...'}
              change="Compliant"
              trend="neutral"
              icon={<Shield className="h-5 w-5" />}
              highlight
              dataSource="Unity Catalog: cfo_banking_demo.silver_finance.securities (SUM market_value) → HQLA eligible securities for regulatory compliance → agent_tools.get_portfolio_summary()"
            />
          </div>
        </div>

        {/* Portfolio & Risk Analysis Tabs */}
        <Tabs defaultValue="portfolio" className="space-y-6 mb-8">
          <TabsList>
            <TabsTrigger value="portfolio">
              Portfolio
            </TabsTrigger>
            <TabsTrigger value="risk">
              Risk Analysis
            </TabsTrigger>
            <TabsTrigger value="activity">
              Recent Activity
            </TabsTrigger>
          </TabsList>

          <TabsContent value="portfolio" className="space-y-6">
            <div className="grid grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <div className="flex items-center">
                    <CardTitle>Loan Portfolio by Product</CardTitle>
                    <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio → Aggregated by product_type with current_balance, interest_rate, and cecl_reserve" />
                  </div>
                </CardHeader>
                <CardContent>
                  <PortfolioBreakdown type="loans" />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <div className="flex items-center">
                    <CardTitle>Deposit Portfolio by Product</CardTitle>
                    <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts → Aggregated by product_type with current_balance and stated_rate" />
                  </div>
                </CardHeader>
                <CardContent>
                  <PortfolioBreakdown type="deposits" />
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="risk" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <CardTitle>Risk Analytics & Stress Testing</CardTitle>
                  <DataSourceTooltip source="Credit Risk: cfo_banking_demo.silver_finance.loan_portfolio (NPL rates, CECL reserves) | Rate Shock: agent_tools.call_deposit_beta_model() with 100 bps stress | LCR: agent_tools.calculate_lcr() with 1.0x and 1.5x multipliers" />
                </div>
                <p className="text-sm text-slate-600">Credit risk metrics and rate shock scenarios</p>
              </CardHeader>
              <CardContent>
                <RiskMetrics />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-6">
            <Card>
              <CardHeader>
                <div className="flex items-center">
                  <CardTitle>Recent Activity</CardTitle>
                  <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio → Last 10 loan originations ordered by origination_date DESC" />
                </div>
                <p className="text-sm text-slate-600">Latest loan originations and transactions</p>
              </CardHeader>
              <CardContent>
                <RecentActivity />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Market & Liquidity Charts */}
        <div className="grid grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <div className="flex items-center">
                <h3 className="text-lg font-bold leading-none tracking-wider font-mono uppercase" style={{ color: '#ff8c00 !important' }}>
                  US TREASURY YIELD CURVE
                </h3>
                <DataSourceTooltip source="Alpha Vantage API → agent_tools.get_current_treasury_yields() → U.S. Department of Treasury daily rates" />
              </div>
              <p className="text-sm font-mono" style={{ color: '#999999' }}>Live market data</p>
            </CardHeader>
            <CardContent>
              <YieldCurveChart />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <div className="flex items-center">
                <h3 className="text-lg font-bold leading-none tracking-wider font-mono uppercase" style={{ color: '#ff8c00 !important' }}>
                  30-DAY LIQUIDITY ANALYSIS
                </h3>
                <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts + silver_finance.securities → agent_tools.calculate_lcr()" />
              </div>
              <p className="text-sm font-mono" style={{ color: '#999999' }}>LCR components</p>
            </CardHeader>
            <CardContent>
              <LiquidityWaterfall />
            </CardContent>
          </Card>
        </div>
          </>
        )}

        {/* Loan Detail Panel (Modal) */}
        {selectedLoan && (
          <LoanDetailPanel
            loanId={selectedLoan}
            open={!!selectedLoan}
            onClose={() => setSelectedLoan(null)}
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
