'use client'

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
