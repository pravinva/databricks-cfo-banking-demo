#!/usr/bin/env python3
"""
WS6-01: Create SOPHISTICATED React Components
World-class, production-grade components with advanced visualizations
"""

from pathlib import Path

def create_sophisticated_yield_curve_chart(base):
    """Create sophisticated yield curve chart with gradient fills"""
    content = ''''use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'

interface YieldData {
  maturity: string
  yield: number
  order: number
}

export default function YieldCurveChart() {
  const [data, setData] = useState<YieldData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchYieldCurve()
    // Refresh every 5 minutes
    const interval = setInterval(fetchYieldCurve, 300000)
    return () => clearInterval(interval)
  }, [])

  const fetchYieldCurve = async () => {
    try {
      const res = await fetch('/api/data/yield-curve')
      const result = await res.json()

      const formatted: YieldData[] = [
        { maturity: '3M', yield: parseFloat(result['3M']), order: 1 },
        { maturity: '2Y', yield: parseFloat(result['2Y']), order: 2 },
        { maturity: '5Y', yield: parseFloat(result['5Y']), order: 3 },
        { maturity: '10Y', yield: parseFloat(result['10Y']), order: 4 },
        { maturity: '30Y', yield: parseFloat(result['30Y']), order: 5 },
      ]
      setData(formatted)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch yield curve:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-700"></div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#1e40af" stopOpacity={0.3}/>
            <stop offset="95%" stopColor="#1e40af" stopOpacity={0}/>
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />

        <XAxis
          dataKey="maturity"
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
        />

        <YAxis
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
          tickFormatter={(value) => `${value.toFixed(2)}%`}
          domain={['dataMin - 0.5', 'dataMax + 0.5']}
        />

        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            padding: '12px'
          }}
          labelStyle={{ fontWeight: 600, marginBottom: '4px' }}
          formatter={(value: number) => [`${value.toFixed(2)}%`, 'Yield']}
        />

        <Area
          type="monotone"
          dataKey="yield"
          stroke="#1e40af"
          strokeWidth={3}
          fill="url(#yieldGradient)"
          animationDuration={1000}
          animationEasing="ease-in-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
'''

    file_path = base / "components" / "charts" / "YieldCurveChart.tsx"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✓ Created: {file_path}")

def create_sophisticated_waterfall_chart(base):
    """Create sophisticated liquidity waterfall chart"""
    content = ''''use client'

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, ReferenceLine } from 'recharts'

interface WaterfallData {
  name: string
  value: number
  fill: string
}

export default function LiquidityWaterfall() {
  const [data, setData] = useState<WaterfallData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLCR()
  }, [])

  const fetchLCR = async () => {
    try {
      const res = await fetch('/api/data/lcr')
      const result = await res.json()

      const waterfall: WaterfallData[] = [
        {
          name: 'HQLA',
          value: result.hqla / 1e9,
          fill: '#10b981'
        },
        {
          name: 'Outflows',
          value: -(result.net_outflows - result.hqla) / 1e9,
          fill: '#dc2626'
        },
        {
          name: 'Net Cash',
          value: result.net_outflows / 1e9,
          fill: '#1e40af'
        }
      ]
      setData(waterfall)
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch LCR:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-[300px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-700"></div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />

        <XAxis
          dataKey="name"
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
        />

        <YAxis
          stroke="#64748b"
          fontSize={12}
          tickLine={false}
          axisLine={{ stroke: '#cbd5e1' }}
          tickFormatter={(value) => `$${Math.abs(value).toFixed(1)}B`}
        />

        <Tooltip
          contentStyle={{
            backgroundColor: 'white',
            border: '1px solid #e2e8f0',
            borderRadius: '8px',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            padding: '12px'
          }}
          formatter={(value: number) => [`$${Math.abs(value).toFixed(2)}B`, '']}
        />

        <ReferenceLine y={0} stroke="#cbd5e1" strokeWidth={2} />

        <Bar dataKey="value" radius={[8, 8, 0, 0]} animationDuration={1000}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
'''

    file_path = base / "components" / "charts" / "LiquidityWaterfall.tsx"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✓ Created: {file_path}")

def create_sophisticated_metric_card(base):
    """Create sophisticated metric card with animations"""
    content = ''''use client'

import { motion } from 'framer-motion'
import { LucideIcon } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  highlight?: boolean
}

export default function MetricCard({
  title,
  value,
  change,
  trend,
  icon,
  highlight = false
}: MetricCardProps) {

  const trendColors = {
    up: 'text-green-600 bg-green-50 border-green-200',
    down: 'text-red-600 bg-red-50 border-red-200',
    neutral: 'text-slate-600 bg-slate-50 border-slate-200'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{
        y: -4,
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
      }}
    >
      <div
        className={`bg-white rounded-lg border shadow-sm p-6 transition-all duration-200 ${
          highlight ? 'ring-2 ring-primary-500 ring-offset-2' : 'border-slate-200'
        }`}
      >
        <div className="flex items-start justify-between mb-4">
          <motion.div
            className={`p-2 rounded-lg ${trendColors[trend]}`}
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            {icon}
          </motion.div>
          <div
            className={`text-xs font-medium px-2 py-1 rounded border ${trendColors[trend]}`}
          >
            {change}
          </div>
        </div>

        <div>
          <p className="text-sm text-slate-600 mb-1 font-medium">{title}</p>
          <motion.p
            className="text-3xl font-bold text-slate-900"
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            {value}
          </motion.p>
        </div>
      </div>
    </motion.div>
  )
}
'''

    file_path = base / "components" / "MetricCard.tsx"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✓ Created: {file_path}")

def create_sophisticated_ai_assistant(base):
    """Create sophisticated AI chat interface"""
    content = ''''use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Sparkles } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          session_id: 'demo_session'
        })
      })

      const data = await response.json()

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const exampleQueries = [
    'Current 10Y Treasury yield',
    'Rate shock: +50 bps on MMDA',
    'LCR status',
    'Portfolio summary'
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto">
        <Card className="border-slate-200 shadow-lg overflow-hidden">
          {/* Header */}
          <div className="border-b border-slate-200 bg-white p-6">
            <div className="flex items-center gap-3">
              <motion.div
                animate={{ rotate: [0, 360] }}
                transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
              >
                <Sparkles className="h-6 w-6 text-primary-700" />
              </motion.div>
              <div>
                <h1 className="text-2xl font-semibold text-slate-900">AI Assistant</h1>
                <p className="text-sm text-slate-600 mt-1">
                  Powered by Claude Sonnet 4.5 with MLflow tracing
                </p>
              </div>
            </div>
          </div>

          {/* Example Queries */}
          <div className="bg-slate-50 p-4 border-b border-slate-200">
            <p className="text-xs font-medium text-slate-600 mb-2">Quick queries:</p>
            <div className="flex gap-2 flex-wrap">
              {exampleQueries.map(query => (
                <motion.button
                  key={query}
                  onClick={() => setInput(query)}
                  className="text-xs px-3 py-1.5 rounded-md bg-white border border-slate-300 hover:border-primary-500 hover:bg-primary-50 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {query}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4 bg-white">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-slate-400">
                <div className="text-center">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">Ask me about Treasury, Risk, or Regulatory metrics</p>
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-primary-700 text-white'
                        : 'bg-slate-100 border border-slate-200 text-slate-900'
                    }`}
                  >
                    <div className="prose prose-sm max-w-none">
                      <pre className="whitespace-pre-wrap font-sans">{message.content}</pre>
                    </div>
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-primary-200' : 'text-slate-500'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-slate-100 border border-slate-200 rounded-lg p-4">
                  <Loader2 className="h-5 w-5 animate-spin text-primary-700" />
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-200 bg-white p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                placeholder="Ask about Treasury, Risk, or Regulatory metrics..."
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                disabled={loading}
              />
              <Button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="bg-primary-700 hover:bg-primary-800 text-white px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
'''

    file_path = base / "app" / "assistant" / "page.tsx"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✓ Created: {file_path}")

def create_sophisticated_main_dashboard(base):
    """Create sophisticated main dashboard page"""
    content = ''''use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, Shield } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import YieldCurveChart from '@/components/charts/YieldCurveChart'
import LiquidityWaterfall from '@/components/charts/LiquidityWaterfall'
import MetricCard from '@/components/MetricCard'
import Link from 'next/link'

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
                CFO Platform
              </h1>
              <p className="text-sm text-slate-600">
                Databricks Financial Services
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
          />
          <MetricCard
            title="Total Deposits"
            value={summary?.success ? `$${(summary.deposits / 1e9).toFixed(1)}B` : 'Loading...'}
            change="+1.8%"
            trend="up"
            icon={<Activity className="h-5 w-5" />}
          />
          <MetricCard
            title="Loans"
            value={summary?.success ? `$${(summary.loans / 1e9).toFixed(1)}B` : 'Loading...'}
            change="-12 bps"
            trend="down"
            icon={<TrendingDown className="h-5 w-5" />}
          />
          <MetricCard
            title="Securities"
            value={summary?.success ? `$${(summary.securities / 1e9).toFixed(1)}B` : 'Loading...'}
            change="Compliant"
            trend="neutral"
            icon={<Shield className="h-5 w-5" />}
            highlight
          />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-2 gap-6 mb-8">
          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-slate-900">
                US Treasury Yield Curve
              </CardTitle>
              <p className="text-sm text-slate-600">Live market data</p>
            </CardHeader>
            <CardContent>
              <YieldCurveChart />
            </CardContent>
          </Card>

          <Card className="border-slate-200 shadow-sm hover:shadow-md transition-shadow">
            <CardHeader>
              <CardTitle className="text-lg font-semibold text-slate-900">
                30-Day Liquidity Analysis
              </CardTitle>
              <p className="text-sm text-slate-600">LCR components</p>
            </CardHeader>
            <CardContent>
              <LiquidityWaterfall />
            </CardContent>
          </Card>
        </div>

        {/* Tabs Section */}
        <Tabs defaultValue="portfolio" className="space-y-6">
          <TabsList className="bg-white border border-slate-200">
            <TabsTrigger value="portfolio">Portfolio</TabsTrigger>
            <TabsTrigger value="risk">Risk Analysis</TabsTrigger>
            <TabsTrigger value="activity">Recent Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="portfolio" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Portfolio Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-slate-600">
                  Advanced portfolio analytics coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="risk" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Risk Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-slate-600">
                  Risk analytics and stress testing coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Activity</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-slate-600">
                  Activity logs coming soon...
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
'''

    file_path = base / "app" / "page.tsx"
    with open(file_path, "w") as f:
        f.write(content)
    print(f"✓ Created (overwriting): {file_path}")

def main():
    base = Path("frontend_app")

    if not base.exists():
        print("Error: frontend_app directory not found!")
        print("Run 16_create_react_frontend.py first")
        return

    print("="*60)
    print("Creating SOPHISTICATED React Components")
    print("="*60)
    print()

    # Create sophisticated components
    create_sophisticated_yield_curve_chart(base)
    create_sophisticated_waterfall_chart(base)
    create_sophisticated_metric_card(base)
    create_sophisticated_ai_assistant(base)
    create_sophisticated_main_dashboard(base)

    print()
    print("="*60)
    print("✅ Sophisticated Components Created!")
    print("="*60)
    print()
    print("Components include:")
    print("  - Advanced yield curve with gradient fills")
    print("  - Sophisticated waterfall chart")
    print("  - Animated metric cards with hover effects")
    print("  - AI chat interface with framer-motion animations")
    print("  - Main dashboard with live data updates")
    print()
    print("Next: cd frontend_app && npm install && npm run dev")

if __name__ == "__main__":
    main()
