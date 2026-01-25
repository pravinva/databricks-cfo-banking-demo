'use client'

import { ChevronRight, Home } from 'lucide-react'
import { useDrillDown } from '@/lib/drill-down-context'

export default function Breadcrumbs() {
  const { state, navigateBack, reset } = useDrillDown()

  if (state.breadcrumbs.length <= 1) return null

  return (
    <div className="flex items-center gap-2 mb-6 text-sm">
      <button
        onClick={reset}
        className="flex items-center gap-1 text-slate-600 hover:text-blue-600 transition-colors"
      >
        <Home className="h-4 w-4" />
      </button>

      {state.breadcrumbs.map((crumb, index) => (
        <div key={index} className="flex items-center gap-2">
          <ChevronRight className="h-4 w-4 text-slate-400" />

          <button
            onClick={() => {
              // Navigate to this level
              if (index < state.breadcrumbs.length - 1) {
                for (let i = 0; i < state.breadcrumbs.length - index - 1; i++) {
                  navigateBack()
                }
              }
            }}
            className={`${
              index === state.breadcrumbs.length - 1
                ? 'text-slate-900 font-medium'
                : 'text-slate-600 hover:text-blue-600'
            } transition-colors`}
          >
            {crumb.label}
          </button>
        </div>
      ))}
    </div>
  )
}
