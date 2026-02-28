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
    up: 'text-bloomberg-green',
    down: 'text-bloomberg-red bloomberg-glow-red',
    neutral: 'text-bloomberg-amber'
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{
        y: -4,
        boxShadow: '0 10px 24px rgba(15, 23, 42, 0.08)'
      }}
    >
      <div
        className={`bloomberg-panel p-5 transition-all duration-200 relative border ${
          highlight ? 'border-bloomberg-orange/60' : 'border-bloomberg-border hover:border-bloomberg-orange/40'
        }`}
      >
        {dataSource && (
          <div className="group absolute top-3 right-3">
            <Info className="h-4 w-4 text-bloomberg-text-dim cursor-help" />
            <div className="absolute top-full right-0 mt-2 hidden group-hover:block z-50 w-72">
              <div className="bg-white border border-bloomberg-border text-bloomberg-text text-xs p-3 shadow-lg rounded-lg">
                <div className="font-bold mb-1 text-bloomberg-orange">DATA SOURCE</div>
                <div className="text-bloomberg-text-dim text-[10px]">{dataSource}</div>
              </div>
            </div>
          </div>
        )}

        <div className="flex items-start justify-between mb-4">
          <motion.div
            className={`${trendColors[trend]}`}
            whileHover={{ scale: 1.1 }}
            transition={{ type: "spring", stiffness: 400, damping: 10 }}
          >
            {icon}
          </motion.div>
          <div
            className={`text-xs font-semibold px-2 py-1 ${trendColors[trend]}`}
          >
            {change}
          </div>
        </div>

        <div>
          <p className="text-xs text-bloomberg-text-dim mb-2 font-semibold tracking-wide">{title.toUpperCase()}</p>
          <motion.p
            className="text-3xl font-semibold text-bloomberg-text tabular-nums"
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
