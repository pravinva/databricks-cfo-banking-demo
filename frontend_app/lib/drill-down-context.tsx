'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

interface DrillDownState {
  view: string
  filters: Record<string, any>
  breadcrumbs: Array<{ label: string; view: string; filters: any }>
}

interface DrillDownContextType {
  state: DrillDownState
  navigateTo: (view: string, filters?: any, label?: string) => void
  navigateBack: () => void
  reset: () => void
}

const DrillDownContext = createContext<DrillDownContextType | undefined>(undefined)

export function DrillDownProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<DrillDownState>({
    view: 'dashboard',
    filters: {},
    breadcrumbs: [{ label: 'Dashboard', view: 'dashboard', filters: {} }]
  })

  const navigateTo = (view: string, filters: any = {}, label: string = view) => {
    setState(prev => ({
      view,
      filters,
      breadcrumbs: [...prev.breadcrumbs, { label, view, filters }]
    }))
  }

  const navigateBack = () => {
    setState(prev => {
      if (prev.breadcrumbs.length <= 1) return prev

      const newBreadcrumbs = prev.breadcrumbs.slice(0, -1)
      const lastCrumb = newBreadcrumbs[newBreadcrumbs.length - 1]

      return {
        view: lastCrumb.view,
        filters: lastCrumb.filters,
        breadcrumbs: newBreadcrumbs
      }
    })
  }

  const reset = () => {
    setState({
      view: 'dashboard',
      filters: {},
      breadcrumbs: [{ label: 'Dashboard', view: 'dashboard', filters: {} }]
    })
  }

  return (
    <DrillDownContext.Provider value={{ state, navigateTo, navigateBack, reset }}>
      {children}
    </DrillDownContext.Provider>
  )
}

export const useDrillDown = () => {
  const context = useContext(DrillDownContext)
  if (!context) throw new Error('useDrillDown must be used within DrillDownProvider')
  return context
}
