'use client'

import { useEffect, useState } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart } from 'recharts'
import { apiFetch } from '@/lib/api'

interface YieldData {
  maturity: string
  yield: number
  order: number
}

export default function YieldCurveChart({ height = 300 }: { height?: number }) {
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
      const res = await apiFetch('/api/data/yield-curve')
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
      <div className="flex items-center justify-center" style={{ height }}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bloomberg-orange"></div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="yieldGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ff8c00" stopOpacity={0.4}/>
            <stop offset="95%" stopColor="#ff8c00" stopOpacity={0}/>
          </linearGradient>
        </defs>

        <CartesianGrid strokeDasharray="3 3" stroke="#333333" vertical={false} />

        <XAxis
          dataKey="maturity"
          stroke="#999999"
          fontSize={12}
          fontFamily="'Courier New', Monaco, Menlo, monospace"
          tickLine={false}
          axisLine={{ stroke: '#333333' }}
        />

        <YAxis
          stroke="#999999"
          fontSize={12}
          fontFamily="'Courier New', Monaco, Menlo, monospace"
          tickLine={false}
          axisLine={{ stroke: '#333333' }}
          tickFormatter={(value) => `${value.toFixed(2)}%`}
          domain={['dataMin - 0.5', 'dataMax + 0.5']}
        />

        <Tooltip
          contentStyle={{
            backgroundColor: '#1a1a1a',
            border: '2px solid #ff8c00',
            borderRadius: '0',
            boxShadow: '0 0 20px rgba(255, 140, 0, 0.3)',
            padding: '12px',
            fontFamily: "'Courier New', Monaco, Menlo, monospace",
            color: '#ffffff'
          }}
          labelStyle={{ fontWeight: 700, marginBottom: '4px', color: '#ff8c00' }}
          formatter={(value: number) => [`${value.toFixed(2)}%`, 'Yield']}
        />

        <Area
          type="monotone"
          dataKey="yield"
          stroke="#ff8c00"
          strokeWidth={3}
          fill="url(#yieldGradient)"
          animationDuration={1000}
          animationEasing="ease-in-out"
        />
      </AreaChart>
    </ResponsiveContainer>
  )
}
