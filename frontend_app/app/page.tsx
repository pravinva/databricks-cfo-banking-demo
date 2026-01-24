'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, Shield, Info } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import YieldCurveChart from '@/components/charts/YieldCurveChart'
import LiquidityWaterfall from '@/components/charts/LiquidityWaterfall'
import MetricCard from '@/components/MetricCard'
import Link from 'next/link'

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
          className="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
        >
          <div>
            <div className="font-medium text-slate-900">{item[0]}</div>
            <div className="text-xs text-slate-600">{Number(item[1]).toLocaleString()} accounts</div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-slate-900">${Number(item[2]).toFixed(2)}B</div>
            <div className="text-xs text-slate-600">{Number(item[3]).toFixed(2)}% avg rate</div>
          </div>
        </div>
      ))}
    </div>
  )
}

function RiskMetrics() {
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)

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
            <div key={index} className="p-3 border border-slate-200 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <div className="font-medium text-slate-900">{item[0]}</div>
                <div className="text-sm font-semibold text-slate-900">${Number(item[1]).toFixed(2)}B</div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                <div>NPL Rate: {Number(item[2]).toFixed(2)}%</div>
                <div>Reserves: ${Number(item[3]).toFixed(2)}B</div>
                <div className="col-span-2">Reserve Ratio: {Number(item[4]).toFixed(2)}%</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="font-semibold text-slate-900">Rate Shock Stress (100 bps)</h3>
        <div className="space-y-3">
          {data.rate_shock_stress?.map((item: any, index: number) => (
            <div key={index} className="p-3 border border-slate-200 rounded-lg">
              <div className="flex justify-between items-start mb-2">
                <div className="font-medium text-slate-900">{item.product}</div>
                <div className="text-sm text-red-600 font-semibold">
                  -${(item.runoff_100bps / 1e6).toFixed(1)}M
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs text-slate-600">
                <div>Beta: {item.beta.toFixed(4)}</div>
                <div>Runoff: {item.runoff_pct.toFixed(2)}%</div>
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg mt-4">
          <h4 className="font-medium text-slate-900 mb-2">LCR Stress Test</h4>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <div className="text-xs text-slate-600">Base Case</div>
              <div className="font-semibold text-slate-900">
                {data.lcr_stress?.base.ratio.toFixed(2)}%
              </div>
              <div className={`text-xs ${data.lcr_stress?.base.status === 'Pass' ? 'text-green-600' : 'text-red-600'}`}>
                {data.lcr_stress?.base.status}
              </div>
            </div>
            <div>
              <div className="text-xs text-slate-600">1.5x Stress</div>
              <div className="font-semibold text-slate-900">
                {data.lcr_stress?.stressed.ratio.toFixed(2)}%
              </div>
              <div className={`text-xs ${data.lcr_stress?.stressed.status === 'Pass' ? 'text-green-600' : 'text-red-600'}`}>
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
          className="flex items-center justify-between p-3 border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
        >
          <div className="flex items-center gap-4">
            <div className="flex flex-col">
              <div className="font-medium text-slate-900">{item[0]}</div>
              <div className="text-xs text-slate-600">{item[1]}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="font-semibold text-slate-900">${(Number(item[2]) / 1000).toFixed(1)}K</div>
            <div className="text-xs text-slate-600">{new Date(item[3]).toLocaleDateString()}</div>
          </div>
        </div>
      ))}
    </div>
  )
}

export default function Dashboard() {
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)

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
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">
                Bank CFO Command Center
              </h1>
              <p className="text-sm text-slate-600">
                Powered by Databricks Lakehouse
              </p>
            </div>

            <div className="flex items-center gap-6">
              <Link
                href="/assistant"
                className="text-sm font-medium text-primary-700 hover:text-primary-900 transition-colors"
              >
                AI Assistant →
              </Link>
              <div className="flex items-center gap-4 text-sm text-slate-600">
                <span>Last updated: {new Date().toLocaleTimeString()}</span>
                <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
                <span className="text-green-600 font-medium">Live</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">

        {/* KPI Cards Row */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Assets"
            value={summary?.success ? `$${(summary.total_assets / 1e9).toFixed(1)}B` : 'Loading...'}
            change="+2.1%"
            trend="up"
            icon={<TrendingUp className="h-5 w-5" />}
            dataSource="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio (SUM current_balance) + silver_finance.securities (SUM market_value) → agent_tools.get_portfolio_summary()"
          />
          <MetricCard
            title="Total Deposits"
            value={summary?.success ? `$${(summary.deposits / 1e9).toFixed(1)}B` : 'Loading...'}
            change="+1.8%"
            trend="up"
            icon={<Activity className="h-5 w-5" />}
            dataSource="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts WHERE account_status = 'Active' (SUM current_balance) → agent_tools.get_portfolio_summary()"
          />
          <MetricCard
            title="Loans"
            value={summary?.success ? `$${(summary.loans / 1e9).toFixed(1)}B` : 'Loading...'}
            change="-12 bps"
            trend="down"
            icon={<TrendingDown className="h-5 w-5" />}
            dataSource="Unity Catalog: cfo_banking_demo.silver_finance.loan_portfolio WHERE is_current = true (SUM current_balance) → agent_tools.get_portfolio_summary()"
          />
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

        {/* Portfolio & Risk Analysis Tabs */}
        <Tabs defaultValue="portfolio" className="space-y-6 mb-8">
          <TabsList className="bg-white border border-slate-200 shadow-sm p-1 rounded-lg">
            <TabsTrigger
              value="portfolio"
              className="data-[state=active]:bg-primary-50 data-[state=active]:text-primary-900 data-[state=active]:border data-[state=active]:border-primary-200 hover:bg-slate-50 transition-all"
            >
              Portfolio
            </TabsTrigger>
            <div className="w-px h-6 bg-slate-200 mx-1"></div>
            <TabsTrigger
              value="risk"
              className="data-[state=active]:bg-primary-50 data-[state=active]:text-primary-900 data-[state=active]:border data-[state=active]:border-primary-200 hover:bg-slate-50 transition-all"
            >
              Risk Analysis
            </TabsTrigger>
            <div className="w-px h-6 bg-slate-200 mx-1"></div>
            <TabsTrigger
              value="activity"
              className="data-[state=active]:bg-primary-50 data-[state=active]:text-primary-900 data-[state=active]:border data-[state=active]:border-primary-200 hover:bg-slate-50 transition-all"
            >
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
          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center">
                <CardTitle className="text-lg font-semibold text-slate-900">
                  US Treasury Yield Curve
                </CardTitle>
                <DataSourceTooltip source="Alpha Vantage API → agent_tools.get_current_treasury_yields() → U.S. Department of Treasury daily rates" />
              </div>
              <p className="text-sm text-slate-600">Live market data</p>
            </CardHeader>
            <CardContent>
              <YieldCurveChart />
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader>
              <div className="flex items-center">
                <CardTitle className="text-lg font-semibold text-slate-900">
                  30-Day Liquidity Analysis
                </CardTitle>
                <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.bronze_core_banking.deposit_accounts + silver_finance.securities → agent_tools.calculate_lcr()" />
              </div>
              <p className="text-sm text-slate-600">LCR components</p>
            </CardHeader>
            <CardContent>
              <LiquidityWaterfall />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  )
}
