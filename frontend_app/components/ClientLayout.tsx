'use client'

import FloatingAIAssistant from './FloatingAIAssistant'
import { usePathname } from 'next/navigation'

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()

  // Don't show floating assistant on the assistant page itself
  const showFloatingAssistant = pathname !== '/assistant'

  return (
    <>
      {children}
      {showFloatingAssistant && <FloatingAIAssistant />}
    </>
  )
}
