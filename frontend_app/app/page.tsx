'use client'

import { useState, useEffect } from 'react'
import { TrendingUp, Activity, Info, LayoutDashboard, Landmark, WalletCards, MessageSquare, Home } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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

type SidebarSection =
  | 'dashboard'
  | 'deposits'
  | 'deposit-beta'
  | 'vintage'
  | 'stress-test'
  | 'ppnr'
  | 'ppnr-scenarios'
  | 'genie'

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

  const compactData = data.slice(0, 6)

  return (
    <div className="space-y-2">
      <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
        {compactData.map((item: any, index: number) => (
          <div
            key={index}
            onClick={() => navigateTo('deposit-table', { product_type: item[0] }, `${item[0]} Deposits`)}
            className="flex items-center justify-between p-3 border border-bloomberg-border bg-bloomberg-surface hover:border-bloomberg-orange/70 transition-colors group cursor-pointer"
          >
            <div>
              <div className="font-bold text-bloomberg-orange group-hover:text-bloomberg-amber transition-colors font-mono text-sm">{item[0]}</div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{Number(item[1]).toLocaleString()} accounts</div>
            </div>
            <div className="text-right">
              <div className="font-bold text-bloomberg-text font-mono text-base">${Number(item[2]).toFixed(2)}B</div>
              <div className="text-xs text-bloomberg-text-dim font-mono mt-1">{Number(item[3]).toFixed(2)}% avg rate</div>
            </div>
          </div>
        ))}
      </div>
      {data.length > compactData.length ? (
        <div className="text-[11px] text-bloomberg-text-dim font-mono">
          Showing top {compactData.length} products. Open Deposits drill-down for full list.
        </div>
      ) : null}
    </div>
  )
}

function DashboardContent() {
  const publishedDashboardUrl =
    'https://e2-demo-field-eng.cloud.databricks.com/dashboardsv3/01f108f1192218ecb07e67641bdc54ed/published?o=1444828305810485'
  const genieRoomUrl =
    'https://e2-demo-field-eng.cloud.databricks.com/genie/rooms/01f101adda151c09835a99254d4c308c?o=1444828305810485'
  const demoDocumentationUrl =
    'https://pravinva.github.io/databricks-cfo-banking-demo/documentation_index.html'
  const treasuryDataHubUrl = 'https://cfo-office-hub-3036928383961086.aws.databricksapps.com/'
  const [summary, setSummary] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [depositBetaMetrics, setDepositBetaMetrics] = useState<any>(null)
  const [ppnrLatest, setPpnrLatest] = useState<any>(null)
  const [ppnrScenarioSummary, setPpnrScenarioSummary] = useState<any[]>([])
  const [latestExecutiveReport, setLatestExecutiveReport] = useState<any>(null)
  const [executiveReportLoading, setExecutiveReportLoading] = useState<boolean>(false)
  const [executiveReportStatusText, setExecutiveReportStatusText] = useState<string>('')
  const [executiveReportStatusTone, setExecutiveReportStatusTone] = useState<
    'idle' | 'generating' | 'done' | 'failed'
  >('idle')
  const [currentTime, setCurrentTime] = useState<string>('')
  const [activeSection, setActiveSection] = useState<SidebarSection>('dashboard')
  const [selectedDepositAccountId, setSelectedDepositAccountId] = useState<string | null>(null)
  const { state, navigateTo, reset } = useDrillDown()

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
        const [betaRes, ppnrRes, ppnrScenarioRes] = await Promise.all([
          apiFetch('/api/data/deposit-beta-metrics'),
          apiFetch('/api/data/ppnr-forecasts'),
          apiFetch('/api/data/ppnr-scenario-summary'),
        ])

        const betaJson = await betaRes.json()
        if (betaJson?.success) setDepositBetaMetrics(betaJson.data)

        const ppnrJson = await ppnrRes.json()
        if (ppnrJson?.success && Array.isArray(ppnrJson?.data) && ppnrJson.data.length > 0) {
          setPpnrLatest(ppnrJson.data[ppnrJson.data.length - 1])
        }

        const ppnrScenarioJson = await ppnrScenarioRes.json()
        if (ppnrScenarioJson?.success && Array.isArray(ppnrScenarioJson?.data)) {
          setPpnrScenarioSummary(ppnrScenarioJson.data)
        }
      } catch (e) {
        // KPI cards should fail soft (dashboard tabs still render)
        console.warn('Failed to fetch treasury KPIs:', e)
      }
    }

    fetchTreasuryKpis()
  }, [])

  useEffect(() => {
    const fetchLatestReport = async () => {
      try {
        const res = await apiFetch('/api/reports/executive/latest')
        const json = await res.json()
        if (json?.success) setLatestExecutiveReport(json)
      } catch (e) {
        // fail soft
        console.warn('Failed to fetch latest executive report:', e)
      }
    }
    fetchLatestReport()
  }, [])

  const downloadLatestExecutiveReport = async (format: 'pdf' | 'html') => {
    setExecutiveReportLoading(true)
    try {
      const res = await apiFetch(`/api/reports/executive/download?format=${format}`)
      if (!res.ok) {
        const msg = await res.text()
        throw new Error(msg || `HTTP ${res.status}`)
      }
      const blob = await res.blob()
      const cd = res.headers.get('content-disposition') || ''
      const match = /filename="([^"]+)"/.exec(cd)
      const filename = match?.[1] || `treasury_report_executive_latest.${format}`
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      a.remove()
      window.URL.revokeObjectURL(url)
    } catch (e) {
      console.error('Failed to download executive report:', e)
      alert(`Failed to download report: ${String((e as any)?.message || e)}`)
    } finally {
      setExecutiveReportLoading(false)
    }
  }

  const runExecutiveReportNow = async () => {
    setExecutiveReportLoading(true)
    setExecutiveReportStatusText('Generating PDF report…')
    setExecutiveReportStatusTone('generating')
    try {
      const startPdfPath = latestExecutiveReport?.latest_pdf_path || null
      const startHtmlPath = latestExecutiveReport?.latest_html_path || null

      const storageKey = 'CFO_EXEC_REPORT_JOB_ID'
      const savedJobIdRaw =
        typeof window !== 'undefined' ? window.localStorage.getItem(storageKey) : null
      const savedJobId = savedJobIdRaw && /^\d+$/.test(savedJobIdRaw) ? Number(savedJobIdRaw) : null

      const trigger = async (jobId?: number) => {
        return apiFetch('/api/reports/executive/run', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(jobId ? { job_id: jobId } : {}),
        })
      }

      // Prefer backend auto-discovery (by job name / notebook path). Only fall back to explicit job id if needed.
      let res = await trigger()
      let json: any = null
      try {
        json = await res.json()
      } catch {
        // ignore parse errors
      }

      if (!res.ok || !json?.success) {
        const errMsg = String(json?.error || `HTTP ${res.status}`)
        if (errMsg.includes('CFO_EXEC_REPORT_JOB_ID not set')) {
          // Try a previously saved job id first (if present).
          if (savedJobId != null) {
            res = await trigger(savedJobId)
            json = await res.json()
          }

          if (json?.success) {
            // ok
          } else {
          const input = window.prompt(
            'Enter the Databricks Job ID for the Executive report (used for RUN REPORT NOW):',
            savedJobIdRaw || '',
          )
          if (!input) throw new Error(errMsg)
          const trimmed = input.trim()
          if (!/^\d+$/.test(trimmed)) throw new Error('Job ID must be a number')
          window.localStorage.setItem(storageKey, trimmed)

          res = await trigger(Number(trimmed))
          json = await res.json()
          }
        } else if (errMsg.toLowerCase().includes('does not exist') && savedJobIdRaw) {
          // If user saved an invalid job id earlier, clear it and retry discovery once.
          window.localStorage.removeItem(storageKey)
          res = await trigger()
          json = await res.json()
        }
      }

      if (!json?.success) throw new Error(json?.error || 'Failed to trigger report job')

      const runId: number | null = typeof json?.run_id === 'number' ? json.run_id : null
      const runUrl: string | null = typeof json?.run_url === 'string' ? json.run_url : null

      if (runUrl) {
        // Optional: open the job run in a new tab for debugging/visibility.
        window.open(runUrl, '_blank', 'noopener,noreferrer')
      }

      const startedAt = Date.now()
      const pollMs = 5000
      const timeoutMs = 7 * 60 * 1000
      let lastLifeCycle: string | null = null
      let lastResult: string | null = null

      while (Date.now() - startedAt < timeoutMs) {
        // 1) Poll job run status (best effort)
        if (runId != null) {
          try {
            const statusRes = await apiFetch(`/api/reports/executive/run_status?run_id=${runId}`)
            const statusJson = await statusRes.json()
            const s = statusJson?.status
            if (statusJson?.success && s) {
              lastLifeCycle = String(s.life_cycle_state || '')
              lastResult = s.result_state != null ? String(s.result_state) : null
              if (lastLifeCycle) {
                setExecutiveReportStatusText(
                  lastLifeCycle === 'TERMINATED'
                    ? 'Finalizing report artifacts…'
                    : `Generating PDF report… (${lastLifeCycle})`,
                )
                setExecutiveReportStatusTone('generating')
              }
              if (lastLifeCycle === 'TERMINATED' && lastResult && lastResult !== 'SUCCESS') {
                throw new Error(`Report job failed: ${lastResult}${s.state_message ? ` (${s.state_message})` : ''}`)
              }
            }
          } catch (e) {
            // If status polling fails, keep going and rely on artifact polling.
            console.warn('Failed to poll report run status:', e)
          }
        }

        // 2) Poll latest artifacts and stop when we see a NEW file
        try {
          const latestRes = await apiFetch('/api/reports/executive/latest')
          const latestJson = await latestRes.json()
          if (latestJson?.success) {
            setLatestExecutiveReport(latestJson)

            const pdfPath = latestJson?.latest_pdf_path || null
            const htmlPath = latestJson?.latest_html_path || null
            const pdfChanged = pdfPath && pdfPath !== startPdfPath
            const htmlChanged = htmlPath && htmlPath !== startHtmlPath

            if (pdfChanged) {
              setExecutiveReportStatusText('Done. Latest PDF is ready to download.')
              setExecutiveReportStatusTone('done')
              break
            }

            if (lastLifeCycle === 'TERMINATED' && htmlChanged) {
              // Notebook is coded to allow SUCCESS even if PDF conversion fails.
              setExecutiveReportStatusText('Done. Report artifacts are ready.')
              setExecutiveReportStatusTone('done')
              break
            }
          }
        } catch (e) {
          console.warn('Failed to poll latest executive report artifacts:', e)
        }

        await new Promise((r) => setTimeout(r, pollMs))
      }

      if (Date.now() - startedAt >= timeoutMs) {
        setExecutiveReportStatusText(
          'Still generating… you can keep waiting, or open the job run to check progress.',
        )
        setExecutiveReportStatusTone('generating')
      }
    } catch (e) {
      console.error('Failed to run executive report:', e)
      alert(`Failed to run report: ${String((e as any)?.message || e)}`)
      setExecutiveReportStatusText('Failed to generate report. See console for details.')
      setExecutiveReportStatusTone('failed')
    } finally {
      setExecutiveReportLoading(false)
    }
  }

  const sidebarItemClass = (section: SidebarSection) =>
    [
      'w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors',
      activeSection === section
        ? 'bg-emerald-50 text-emerald-700 border border-emerald-100'
        : 'text-bloomberg-text-dim hover:bg-orange-50 hover:border-bloomberg-orange/60 hover:text-bloomberg-text border border-transparent',
    ].join(' ')

  const handleSidebarSelect = (section: SidebarSection) => {
    if (state.view === 'deposit-table') {
      reset()
    }
    setActiveSection(section)
  }

  return (
    <div className="min-h-screen bg-bloomberg-bg">
      <header className="bloomberg-header sticky top-0 z-50">
        <div className="px-6 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-bloomberg-text tracking-tight">
                Treasury Deposits & PPNR Hub
              </h1>
              <p className="text-xs text-bloomberg-text-dim mt-1">
                Executive Dashboard | Deposits, PPNR, Liquidity and Funding Risk
              </p>
            </div>

            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <a
                  href={demoDocumentationUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-3 py-2 border border-bloomberg-orange rounded-lg bg-orange-50 text-bloomberg-orange text-xs font-semibold transition-colors hover:bg-orange-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bloomberg-orange/40"
                  title="Open GitHub Pages demo documentation"
                >
                  DEMO DOCUMENTATION
                </a>
                <button
                  className="px-3 py-2 border border-bloomberg-green rounded-lg bg-emerald-50 text-bloomberg-green text-xs font-semibold transition-colors disabled:opacity-50 hover:bg-emerald-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bloomberg-green/40"
                  onClick={() => downloadLatestExecutiveReport('pdf')}
                  disabled={executiveReportLoading}
                  title={latestExecutiveReport?.latest_timestamp ? `Latest: ${latestExecutiveReport.latest_timestamp}` : 'Download latest PDF'}
                >
                  {executiveReportLoading ? 'WORKING…' : 'GET DOCUMENT (PDF)'}
                </button>
                <button
                  className="px-3 py-2 border border-bloomberg-border rounded-lg bg-bloomberg-surface text-bloomberg-orange text-xs transition-colors disabled:opacity-50 hover:border-bloomberg-orange hover:bg-orange-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bloomberg-orange/40"
                  onClick={runExecutiveReportNow}
                  disabled={executiveReportLoading}
                  title="Trigger the scheduled notebook/job now"
                >
                  RUN REPORT NOW
                </button>
                {executiveReportStatusText ? (
                  <div
                    className={[
                      'ml-2 text-[11px] max-w-[360px] truncate',
                      executiveReportStatusTone === 'generating'
                        ? 'text-bloomberg-orange'
                        : executiveReportStatusTone === 'done'
                          ? 'text-bloomberg-green'
                          : executiveReportStatusTone === 'failed'
                            ? 'text-bloomberg-orange'
                            : 'text-bloomberg-text-dim',
                    ].join(' ')}
                  >
                    {executiveReportStatusText}
                  </div>
                ) : null}
              </div>
              <div className="flex items-center gap-3 text-xs text-bloomberg-text-dim">
                <span>{currentTime || '--:--:--'}</span>
                <div className="h-2 w-2 rounded-full bg-bloomberg-green animate-pulse" />
                <span className="text-bloomberg-green font-bold">LIVE</span>
              </div>
            </div>
          </div>
        </div>
      </header>
      <div className="flex">
        <aside className="hidden xl:flex xl:w-64 border-r border-bloomberg-border bg-white/80 min-h-[calc(100vh-72px)] p-5">
          <div className="w-full">
            <div className="mb-4 p-2 rounded-lg border border-bloomberg-border bg-white">
              <img
                src="/databank-logo.png"
                alt="DataBank"
                className="w-full h-16 object-contain rounded-md"
              />
            </div>
            <div className="space-y-1 text-sm">
              <a
                href={treasuryDataHubUrl}
                className="w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors text-bloomberg-text-dim hover:bg-orange-50 hover:border-bloomberg-orange/60 hover:text-bloomberg-text border border-transparent"
                title="Return to Treasury Data Hub"
              >
                <Home className="h-4 w-4" />
                Treasury Data Hub
              </a>
              <a
                href={publishedDashboardUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="w-full text-left px-3 py-2 rounded-lg flex items-center gap-2 transition-colors text-bloomberg-text-dim hover:bg-orange-50 hover:border-bloomberg-orange/60 hover:text-bloomberg-text border border-transparent"
              >
                <LayoutDashboard className="h-4 w-4" />
                AI/BI Insights
              </a>
              <button className={sidebarItemClass('dashboard')} onClick={() => handleSidebarSelect('dashboard')}>
                <LayoutDashboard className="h-4 w-4" />
                Portfolio
              </button>
              <button className={sidebarItemClass('deposits')} onClick={() => handleSidebarSelect('deposits')}>
                <Activity className="h-4 w-4" />
                Deposits
              </button>
              <button className={sidebarItemClass('deposit-beta')} onClick={() => handleSidebarSelect('deposit-beta')}>
                <TrendingUp className="h-4 w-4" />
                Deposit Beta
              </button>
              <button className={sidebarItemClass('vintage')} onClick={() => handleSidebarSelect('vintage')}>
                <WalletCards className="h-4 w-4" />
                Vintage Analysis
              </button>
              <button className={sidebarItemClass('stress-test')} onClick={() => handleSidebarSelect('stress-test')}>
                <Landmark className="h-4 w-4" />
                CCAR Stress
              </button>
              <button className={sidebarItemClass('ppnr')} onClick={() => handleSidebarSelect('ppnr')}>
                <WalletCards className="h-4 w-4" />
                PPNR Forecast
              </button>
              <button className={sidebarItemClass('ppnr-scenarios')} onClick={() => handleSidebarSelect('ppnr-scenarios')}>
                <TrendingUp className="h-4 w-4" />
                PPNR Scenarios
              </button>
              <button className={sidebarItemClass('genie')} onClick={() => handleSidebarSelect('genie')}>
                <MessageSquare className="h-4 w-4" />
                Genie Conversation
              </button>
            </div>
          </div>
        </aside>

        <main className="flex-1 px-6 py-6">
        <Breadcrumbs />

        {state.view === 'deposit-table' ? (
          <DepositTable
            filters={state.filters}
            onAccountClick={(accountId) => setSelectedDepositAccountId(accountId)}
          />
        ) : (
          <>
            {activeSection === 'dashboard' && (
              <>
                <div className="grid grid-cols-3 gap-4 mb-6">
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

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
                  <Card className="xl:col-span-3">
                    <CardHeader>
                      <div className="flex items-center">
                        <h3 className="text-base font-semibold leading-none tracking-wide text-bloomberg-text">
                          US TREASURY YIELD CURVE
                        </h3>
                        <DataSourceTooltip source="Alpha Vantage API → agent_tools.get_current_treasury_yields() → U.S. Department of Treasury daily rates" />
                      </div>
                      <p className="text-sm text-bloomberg-text-dim">
                        Live market data (compact view)
                      </p>
                    </CardHeader>
                    <CardContent>
                      <YieldCurveChart height={150} />
                    </CardContent>
                  </Card>

                  <Card className="xl:col-span-9">
                    <CardHeader>
                      <div className="flex items-center">
                        <h3 className="text-base font-semibold leading-none tracking-wide text-bloomberg-text">
                          PPNR SCENARIO PLANNING (ALCO)
                        </h3>
                        <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml (fallback to ppnr_projection_quarterly / ml_models.ppnr_forecasts) via /api/data/ppnr-scenario-summary" />
                      </div>
                      <p className="text-sm text-bloomberg-text-dim">
                        Expanded scenario view: trajectory, cumulative impact, and optional attribution detail
                      </p>
                    </CardHeader>
                    <CardContent>
                      {ppnrScenarioSummary.length === 0 ? (
                        <div className="text-sm text-bloomberg-text-dim font-mono">
                          No PPNR scenario data available yet. Run scenario planning notebooks.
                        </div>
                      ) : (
                        <div className="space-y-4">
                          <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                            {ppnrScenarioSummary.map((row: any, idx: number) => (
                              <div key={idx} className="p-3 border border-bloomberg-border rounded-lg bg-slate-50">
                                <div className="text-xs text-bloomberg-text-dim font-mono uppercase tracking-wider">{row.scenario}</div>
                                <div className="text-base font-bold text-bloomberg-text font-mono mt-1">
                                  Q1 ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                </div>
                                <div className="text-lg font-bold text-bloomberg-text font-mono mt-1">
                                  ${(Number(row.q9_ppnr_usd || 0) / 1e9).toFixed(2)}B
                                </div>
                                <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">Q9 PPNR</div>
                                <div
                                  className={`text-xs font-mono mt-1 ${Number(row.q9_delta_ppnr_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}
                                >
                                  {Number(row.q9_delta_ppnr_usd || 0) >= 0 ? '+' : ''}
                                  ${(Number(row.q9_delta_ppnr_usd || 0) / 1e6).toFixed(0)}M vs baseline
                                </div>
                                <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">
                                  9Q Cum ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(2)}B
                                </div>
                              </div>
                            ))}
                          </div>

                          <div className="overflow-x-auto">
                            <table className="w-full text-xs font-mono">
                              <thead>
                                <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                                  <th className="text-left py-2">Scenario</th>
                                  <th className="text-right py-2">2Y Shock</th>
                                  <th className="text-right py-2">Equity</th>
                                  <th className="text-right py-2">Credit</th>
                                  <th className="text-right py-2">FX</th>
                                  <th className="text-right py-2">Runoff</th>
                                  <th className="text-right py-2">Q1 PPNR</th>
                                  <th className="text-right py-2">Q4 PPNR</th>
                                  <th className="text-right py-2">Q9 PPNR</th>
                                  <th className="text-right py-2">9Q Cumulative</th>
                                </tr>
                              </thead>
                              <tbody>
                                {ppnrScenarioSummary.map((row: any, idx: number) => (
                                  <tr key={idx} className="border-b border-bloomberg-border/40">
                                    <td className="py-2 text-bloomberg-text">{row.scenario}</td>
                                    <td className="py-2 text-right text-bloomberg-text-dim">
                                      {Number(row.rate_2y_delta_bps || 0) >= 0 ? '+' : ''}
                                      {Number(row.rate_2y_delta_bps || 0).toFixed(0)} bps
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text-dim">
                                      {Number(row.equity_shock_pct || 0) >= 0 ? '+' : ''}
                                      {(Number(row.equity_shock_pct || 0) * 100).toFixed(1)}%
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text-dim">
                                      {Number(row.credit_spread_shock_bps || 0) >= 0 ? '+' : ''}
                                      {Number(row.credit_spread_shock_bps || 0).toFixed(0)} bps
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text-dim">
                                      {Number(row.fx_shock_pct || 0) >= 0 ? '+' : ''}
                                      {(Number(row.fx_shock_pct || 0) * 100).toFixed(1)}%
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text-dim">
                                      {Number(row.liquidity_runoff_shock_pct || 0) >= 0 ? '+' : ''}
                                      {(Number(row.liquidity_runoff_shock_pct || 0) * 100).toFixed(1)}%
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text">
                                      ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text">
                                      ${(Number(row.q4_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text">
                                      ${(Number(row.q9_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                    </td>
                                    <td className="py-2 text-right text-bloomberg-text">
                                      ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(1)}B
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>

                          <details className="border border-bloomberg-border rounded-lg bg-slate-50 p-3">
                            <summary className="cursor-pointer text-xs font-mono text-bloomberg-orange uppercase tracking-wider">
                              Show Q9 attribution details (rate / market / liquidity)
                            </summary>
                            <div className="overflow-x-auto mt-3">
                              <table className="w-full text-xs font-mono">
                                <thead>
                                  <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                                    <th className="text-left py-2">Scenario</th>
                                    <th className="text-right py-2">Q9 Δ Total</th>
                                    <th className="text-right py-2">Q9 Δ Rate</th>
                                    <th className="text-right py-2">Q9 Δ Market</th>
                                    <th className="text-right py-2">Q9 Δ Liquidity</th>
                                  </tr>
                                </thead>
                                <tbody>
                                  {ppnrScenarioSummary.map((row: any, idx: number) => (
                                    <tr key={idx} className="border-b border-bloomberg-border/40">
                                      <td className="py-2 text-bloomberg-text">{row.scenario}</td>
                                      <td className={`py-2 text-right ${Number(row.q9_delta_ppnr_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                        {Number(row.q9_delta_ppnr_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                      </td>
                                      <td className={`py-2 text-right ${Number(row.q9_delta_rate_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                        {Number(row.q9_delta_rate_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_rate_usd || 0) / 1e6).toFixed(0)}M
                                      </td>
                                      <td className={`py-2 text-right ${Number(row.q9_delta_market_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                        {Number(row.q9_delta_market_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_market_usd || 0) / 1e6).toFixed(0)}M
                                      </td>
                                      <td className={`py-2 text-right ${Number(row.q9_delta_liquidity_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                        {Number(row.q9_delta_liquidity_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_liquidity_usd || 0) / 1e6).toFixed(0)}M
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          </details>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </div>
              </>
            )}

            {activeSection === 'deposits' && (
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
            )}

            {activeSection === 'deposit-beta' && <DepositBetaDashboard />}
            {activeSection === 'vintage' && <VintageAnalysisDashboard />}
            {activeSection === 'stress-test' && <StressTestDashboard />}
            {activeSection === 'ppnr' && <PpnrDashboard />}
            {activeSection === 'ppnr-scenarios' && (
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <div className="flex items-center">
                      <CardTitle>PPNR Scenario Planning (ALCO)</CardTitle>
                      <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml (fallback to ppnr_projection_quarterly / ml_models.ppnr_forecasts) via /api/data/ppnr-scenario-summary" />
                    </div>
                    <p className="text-sm text-bloomberg-text-dim">
                      Scenario-specific PPNR trajectory with rate, market, and liquidity shocks.
                    </p>
                  </CardHeader>
                  <CardContent>
                    {ppnrScenarioSummary.length === 0 ? (
                      <div className="text-sm text-bloomberg-text-dim font-mono">
                        No PPNR scenario data available yet. Run scenario planning notebooks.
                      </div>
                    ) : (
                      <div className="space-y-4">
                        <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                          {ppnrScenarioSummary.map((row: any, idx: number) => (
                            <div key={idx} className="p-3 border border-bloomberg-border rounded-lg bg-slate-50">
                              <div className="text-xs text-bloomberg-text-dim font-mono uppercase tracking-wider">{row.scenario}</div>
                              <div className="text-base font-bold text-bloomberg-text font-mono mt-1">
                                Q1 ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                              </div>
                              <div className="text-lg font-bold text-bloomberg-text font-mono mt-1">
                                ${(Number(row.q9_ppnr_usd || 0) / 1e9).toFixed(2)}B
                              </div>
                              <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">Q9 PPNR</div>
                              <div
                                className={`text-xs font-mono mt-1 ${Number(row.q9_delta_ppnr_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}
                              >
                                {Number(row.q9_delta_ppnr_usd || 0) >= 0 ? '+' : ''}
                                ${(Number(row.q9_delta_ppnr_usd || 0) / 1e6).toFixed(0)}M vs baseline
                              </div>
                              <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">
                                9Q Cum ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(2)}B
                              </div>
                            </div>
                          ))}
                        </div>

                        <div className="overflow-x-auto">
                          <table className="w-full text-xs font-mono">
                            <thead>
                              <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                                <th className="text-left py-2">Scenario</th>
                                <th className="text-right py-2">2Y Shock</th>
                                <th className="text-right py-2">Equity</th>
                                <th className="text-right py-2">Credit</th>
                                <th className="text-right py-2">FX</th>
                                <th className="text-right py-2">Runoff</th>
                                <th className="text-right py-2">Q1 PPNR</th>
                                <th className="text-right py-2">Q4 PPNR</th>
                                <th className="text-right py-2">Q9 PPNR</th>
                                <th className="text-right py-2">9Q Cumulative</th>
                              </tr>
                            </thead>
                            <tbody>
                              {ppnrScenarioSummary.map((row: any, idx: number) => (
                                <tr key={idx} className="border-b border-bloomberg-border/40">
                                  <td className="py-2 text-bloomberg-text">{row.scenario}</td>
                                  <td className="py-2 text-right text-bloomberg-text-dim">
                                    {Number(row.rate_2y_delta_bps || 0) >= 0 ? '+' : ''}
                                    {Number(row.rate_2y_delta_bps || 0).toFixed(0)} bps
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text-dim">
                                    {Number(row.equity_shock_pct || 0) >= 0 ? '+' : ''}
                                    {(Number(row.equity_shock_pct || 0) * 100).toFixed(1)}%
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text-dim">
                                    {Number(row.credit_spread_shock_bps || 0) >= 0 ? '+' : ''}
                                    {Number(row.credit_spread_shock_bps || 0).toFixed(0)} bps
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text-dim">
                                    {Number(row.fx_shock_pct || 0) >= 0 ? '+' : ''}
                                    {(Number(row.fx_shock_pct || 0) * 100).toFixed(1)}%
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text-dim">
                                    {Number(row.liquidity_runoff_shock_pct || 0) >= 0 ? '+' : ''}
                                    {(Number(row.liquidity_runoff_shock_pct || 0) * 100).toFixed(1)}%
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text">
                                    ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text">
                                    ${(Number(row.q4_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text">
                                    ${(Number(row.q9_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className="py-2 text-right text-bloomberg-text">
                                    ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(1)}B
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}

            {activeSection === 'genie' && (
              <Card>
                <CardHeader>
                  <CardTitle>Genie Conversation</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-sm text-bloomberg-text-dim">
                    Open Genie in Databricks or use the in-app assistant page for conversation tracking.
                  </p>
                  <div className="flex gap-2">
                    <a
                      href={genieRoomUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-2 border border-bloomberg-border rounded-lg bg-bloomberg-surface text-sm hover:border-bloomberg-orange hover:bg-orange-50"
                    >
                      Open Genie Room
                    </a>
                    <button
                      onClick={() => window.dispatchEvent(new Event('open-treasury-genie'))}
                      className="px-3 py-2 border border-bloomberg-border rounded-lg bg-bloomberg-surface text-sm hover:border-bloomberg-orange hover:bg-orange-50"
                    >
                      Open In-App Assistant
                    </button>
                  </div>
                </CardContent>
              </Card>
            )}

            {false && <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
              <Card className="xl:col-span-3">
                <CardHeader>
                  <div className="flex items-center">
                    <h3 className="text-base font-semibold leading-none tracking-wide text-bloomberg-text">
                      US TREASURY YIELD CURVE
                    </h3>
                    <DataSourceTooltip source="Alpha Vantage API → agent_tools.get_current_treasury_yields() → U.S. Department of Treasury daily rates" />
                  </div>
                  <p className="text-sm text-bloomberg-text-dim">
                    Live market data (compact view)
                  </p>
                </CardHeader>
                <CardContent>
                  <YieldCurveChart height={150} />
                </CardContent>
              </Card>

              <Card className="xl:col-span-9">
                <CardHeader>
                  <div className="flex items-center">
                    <h3 className="text-base font-semibold leading-none tracking-wide text-bloomberg-text">
                      PPNR SCENARIO PLANNING (ALCO)
                    </h3>
                    <DataSourceTooltip source="Unity Catalog: cfo_banking_demo.gold_finance.ppnr_projection_quarterly_ml (fallback to ppnr_projection_quarterly / ml_models.ppnr_forecasts) via /api/data/ppnr-scenario-summary" />
                  </div>
                  <p className="text-sm text-bloomberg-text-dim">
                    Expanded scenario view: trajectory, cumulative impact, and optional attribution detail
                  </p>
                </CardHeader>
                <CardContent>
                  {ppnrScenarioSummary.length === 0 ? (
                    <div className="text-sm text-bloomberg-text-dim font-mono">
                      No PPNR scenario data available yet. Run scenario planning notebooks.
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">
                        {ppnrScenarioSummary.map((row: any, idx: number) => (
                          <div key={idx} className="p-3 border border-bloomberg-border rounded-lg bg-slate-50">
                            <div className="text-xs text-bloomberg-text-dim font-mono uppercase tracking-wider">{row.scenario}</div>
                            <div className="text-base font-bold text-bloomberg-text font-mono mt-1">
                              Q1 ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                            </div>
                            <div className="text-lg font-bold text-bloomberg-text font-mono mt-1">
                              ${(Number(row.q9_ppnr_usd || 0) / 1e9).toFixed(2)}B
                            </div>
                            <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">Q9 PPNR</div>
                            <div
                              className={`text-xs font-mono mt-1 ${Number(row.q9_delta_ppnr_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}
                            >
                              {Number(row.q9_delta_ppnr_usd || 0) >= 0 ? '+' : ''}
                              ${(Number(row.q9_delta_ppnr_usd || 0) / 1e6).toFixed(0)}M vs baseline
                            </div>
                            <div className="text-xs font-mono mt-1 text-bloomberg-text-dim">
                              9Q Cum ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(2)}B
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="overflow-x-auto">
                        <table className="w-full text-xs font-mono">
                          <thead>
                            <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                              <th className="text-left py-2">Scenario</th>
                              <th className="text-right py-2">2Y Shock</th>
                              <th className="text-right py-2">Equity</th>
                              <th className="text-right py-2">Credit</th>
                              <th className="text-right py-2">FX</th>
                              <th className="text-right py-2">Runoff</th>
                              <th className="text-right py-2">Q1 PPNR</th>
                              <th className="text-right py-2">Q4 PPNR</th>
                              <th className="text-right py-2">Q9 PPNR</th>
                              <th className="text-right py-2">9Q Cumulative</th>
                            </tr>
                          </thead>
                          <tbody>
                            {ppnrScenarioSummary.map((row: any, idx: number) => (
                              <tr key={idx} className="border-b border-bloomberg-border/40">
                                <td className="py-2 text-bloomberg-text">{row.scenario}</td>
                                <td className="py-2 text-right text-bloomberg-text-dim">
                                  {Number(row.rate_2y_delta_bps || 0) >= 0 ? '+' : ''}
                                  {Number(row.rate_2y_delta_bps || 0).toFixed(0)} bps
                                </td>
                                <td className="py-2 text-right text-bloomberg-text-dim">
                                  {Number(row.equity_shock_pct || 0) >= 0 ? '+' : ''}
                                  {(Number(row.equity_shock_pct || 0) * 100).toFixed(1)}%
                                </td>
                                <td className="py-2 text-right text-bloomberg-text-dim">
                                  {Number(row.credit_spread_shock_bps || 0) >= 0 ? '+' : ''}
                                  {Number(row.credit_spread_shock_bps || 0).toFixed(0)} bps
                                </td>
                                <td className="py-2 text-right text-bloomberg-text-dim">
                                  {Number(row.fx_shock_pct || 0) >= 0 ? '+' : ''}
                                  {(Number(row.fx_shock_pct || 0) * 100).toFixed(1)}%
                                </td>
                                <td className="py-2 text-right text-bloomberg-text-dim">
                                  {Number(row.liquidity_runoff_shock_pct || 0) >= 0 ? '+' : ''}
                                  {(Number(row.liquidity_runoff_shock_pct || 0) * 100).toFixed(1)}%
                                </td>
                                <td className="py-2 text-right text-bloomberg-text">
                                  ${(Number(row.q1_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                </td>
                                <td className="py-2 text-right text-bloomberg-text">
                                  ${(Number(row.q4_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                </td>
                                <td className="py-2 text-right text-bloomberg-text">
                                  ${(Number(row.q9_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                </td>
                                <td className="py-2 text-right text-bloomberg-text">
                                  ${(Number(row.cumulative_9q_ppnr_usd || 0) / 1e9).toFixed(1)}B
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      <details className="border border-bloomberg-border rounded-lg bg-slate-50 p-3">
                        <summary className="cursor-pointer text-xs font-mono text-bloomberg-orange uppercase tracking-wider">
                          Show Q9 attribution details (rate / market / liquidity)
                        </summary>
                        <div className="overflow-x-auto mt-3">
                          <table className="w-full text-xs font-mono">
                            <thead>
                              <tr className="text-bloomberg-text-dim border-b border-bloomberg-border">
                                <th className="text-left py-2">Scenario</th>
                                <th className="text-right py-2">Q9 Δ Total</th>
                                <th className="text-right py-2">Q9 Δ Rate</th>
                                <th className="text-right py-2">Q9 Δ Market</th>
                                <th className="text-right py-2">Q9 Δ Liquidity</th>
                              </tr>
                            </thead>
                            <tbody>
                              {ppnrScenarioSummary.map((row: any, idx: number) => (
                                <tr key={idx} className="border-b border-bloomberg-border/40">
                                  <td className="py-2 text-bloomberg-text">{row.scenario}</td>
                                  <td className={`py-2 text-right ${Number(row.q9_delta_ppnr_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                    {Number(row.q9_delta_ppnr_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_ppnr_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className={`py-2 text-right ${Number(row.q9_delta_rate_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                    {Number(row.q9_delta_rate_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_rate_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className={`py-2 text-right ${Number(row.q9_delta_market_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                    {Number(row.q9_delta_market_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_market_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                  <td className={`py-2 text-right ${Number(row.q9_delta_liquidity_usd || 0) >= 0 ? 'text-bloomberg-green' : 'text-bloomberg-red'}`}>
                                    {Number(row.q9_delta_liquidity_usd || 0) >= 0 ? '+' : ''}${(Number(row.q9_delta_liquidity_usd || 0) / 1e6).toFixed(0)}M
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </details>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>}
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
