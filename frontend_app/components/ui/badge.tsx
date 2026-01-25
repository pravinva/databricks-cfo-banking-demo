import * as React from "react"

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'success'
}

function Badge({ className, variant = 'default', ...props }: BadgeProps) {
  const variantClasses = {
    default: 'border-transparent bg-bloomberg-orange text-black hover:bg-bloomberg-orange/80',
    secondary: 'border-transparent bg-bloomberg-surface text-bloomberg-text hover:bg-bloomberg-surface/80',
    destructive: 'border-transparent bg-bloomberg-red text-white hover:bg-bloomberg-red/80',
    outline: 'text-bloomberg-orange border-bloomberg-orange bg-bloomberg-surface',
    success: 'border-transparent bg-bloomberg-green text-black hover:bg-bloomberg-green/80',
  }

  return (
    <div
      className={`inline-flex items-center rounded-none border-2 px-2.5 py-0.5 text-xs font-bold font-mono transition-colors focus:outline-none ${variantClasses[variant]} ${className || ''}`}
      {...props}
    />
  )
}

export { Badge }
