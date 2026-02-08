import * as React from "react"
import { cn } from "@/lib/utils"

const Tabs = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { defaultValue?: string }
>(({ className, defaultValue, children, ...props }, ref) => {
  const [activeTab, setActiveTab] = React.useState(defaultValue)

  return (
    <div ref={ref} className={cn("w-full", className)} {...props}>
      {React.Children.map(children, child => {
        if (!React.isValidElement(child)) return child

        // Works for both function components and React.forwardRef (object type)
        const typeAny = child.type as any
        const displayName = typeAny?.displayName || typeAny?.name

        // Only TabsList needs setActiveTab; TabsContent should not receive it (avoids React DOM warnings)
        const injectedProps = displayName === "TabsList" ? { activeTab, setActiveTab } : { activeTab }

        return React.cloneElement(child as React.ReactElement<any>, injectedProps)
      })}
    </div>
  )
})
Tabs.displayName = "Tabs"

const TabsList = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { activeTab?: string; setActiveTab?: (value: string) => void }
>(({ className, children, activeTab, setActiveTab, ...props }, ref) => {
  // Remove activeTab and setActiveTab from props to prevent React warnings
  const { activeTab: _, setActiveTab: __, ...domProps } = props as any

  return (
    <div
      ref={ref}
      className={cn(
        "flex w-full h-14 items-center bg-bloomberg-surface border-b-2 border-bloomberg-orange/30 p-0 gap-1",
        className
      )}
      {...domProps}
    >
      {React.Children.map(children, child =>
        React.isValidElement(child)
          ? React.cloneElement(child as React.ReactElement<any>, { activeTab, setActiveTab })
          : child
      )}
    </div>
  )
})
TabsList.displayName = "TabsList"

const TabsTrigger = React.forwardRef<
  HTMLButtonElement,
  React.ButtonHTMLAttributes<HTMLButtonElement> & {
    value: string
    activeTab?: string
    setActiveTab?: (value: string) => void
  }
>(({ className, value, activeTab, setActiveTab, ...props }, ref) => (
  <button
    ref={ref}
    className={cn(
      "flex-1 items-center justify-center whitespace-nowrap rounded-none px-6 py-4 text-sm font-bold font-mono uppercase tracking-wider transition-all duration-200 border-b-4 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
      activeTab === value
        ? "bg-bloomberg-surface border-bloomberg-orange text-bloomberg-orange"
        : "bg-transparent border-transparent text-bloomberg-text-dim hover:text-bloomberg-orange hover:bg-bloomberg-surface/50 hover:border-bloomberg-orange/30",
      className
    )}
    onClick={() => setActiveTab?.(value)}
    {...props}
  />
))
TabsTrigger.displayName = "TabsTrigger"

const TabsContent = React.forwardRef<
  HTMLDivElement,
  React.HTMLAttributes<HTMLDivElement> & { value: string; activeTab?: string }
>(({ className, value, activeTab, children, ...props }, ref) => {
  if (activeTab !== value) return null

  return (
    <div
      ref={ref}
      className={cn(
        "mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2",
        className
      )}
      {...props}
    >
      {children}
    </div>
  )
})
TabsContent.displayName = "TabsContent"

export { Tabs, TabsList, TabsTrigger, TabsContent }
