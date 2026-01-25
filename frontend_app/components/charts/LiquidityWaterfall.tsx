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
          fill: '#00ff00'
        },
        {
          name: 'Outflows',
          value: -(result.net_outflows - result.hqla) / 1e9,
          fill: '#ff0000'
        },
        {
          name: 'Net Cash',
          value: result.net_outflows / 1e9,
          fill: '#ff8c00'
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-bloomberg-orange"></div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#333333" vertical={false} />

        <XAxis
          dataKey="name"
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
          tickFormatter={(value) => `$${Math.abs(value).toFixed(1)}B`}
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
          formatter={(value: number) => [`$${Math.abs(value).toFixed(2)}B`, '']}
        />

        <ReferenceLine y={0} stroke="#333333" strokeWidth={2} />

        <Bar dataKey="value" radius={[0, 0, 0, 0]} animationDuration={1000}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
