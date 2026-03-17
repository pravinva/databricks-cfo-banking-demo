'use client'

import { Info } from 'lucide-react'
import type { ReactNode } from 'react'

interface InsightTooltipProps {
  title: string
  text: string
  className?: string
}

export function InsightTooltip({ title, text, className = '' }: InsightTooltipProps) {
  return (
    <div className={`group relative inline-block align-middle ${className}`}>
      <button
        type="button"
        className="text-bloomberg-text-dim hover:text-bloomberg-orange focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-bloomberg-green rounded-full"
        aria-label={title}
      >
        <Info className="h-4 w-4" />
      </button>
      <div className="absolute bottom-full left-1/2 z-50 mb-2 hidden w-72 -translate-x-1/2 group-hover:block group-focus-within:block">
        <div className="rounded-lg border border-bloomberg-border bg-white p-3 text-xs text-bloomberg-text shadow-lg">
          <div className="mb-1 font-semibold text-bloomberg-green">{title}</div>
          <div className="text-[11px] leading-relaxed text-bloomberg-text-dim">{text}</div>
        </div>
      </div>
    </div>
  )
}

interface InsightValueProps {
  value: ReactNode
  title: string
  text: string
  valueClassName?: string
}

export function InsightValue({ value, title, text, valueClassName = '' }: InsightValueProps) {
  return (
    <div className="flex items-center gap-2">
      <div className={valueClassName}>{value}</div>
      <InsightTooltip title={title} text={text} />
    </div>
  )
}
