'use client'

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
