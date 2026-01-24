'use client'

import { motion } from 'framer-motion'
import { LucideIcon, Info } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
  icon: React.ReactNode
  highlight?: boolean
  dataSource?: string
}

export default function MetricCard({
  title,
  value,
  change,
  trend,
  icon,
  highlight = false,
  dataSource
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
        className={`bg-white rounded-lg border shadow-sm p-6 transition-all duration-200 relative ${
          highlight ? 'ring-2 ring-primary-500 ring-offset-2' : 'border-slate-200'
        }`}
      >
        {dataSource && (
          <div className="group absolute top-3 right-3">
            <Info className="h-4 w-4 text-slate-400 cursor-help" />
            <div className="absolute top-full right-0 mt-2 hidden group-hover:block z-50 w-72">
              <div className="bg-slate-900 text-white text-xs rounded-lg p-3 shadow-lg">
                <div className="font-medium mb-1">Data Source</div>
                <div className="text-slate-300">{dataSource}</div>
                <div className="absolute bottom-full right-4 mb-[-4px]">
                  <div className="border-4 border-transparent border-b-slate-900"></div>
                </div>
              </div>
            </div>
          </div>
        )}

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
