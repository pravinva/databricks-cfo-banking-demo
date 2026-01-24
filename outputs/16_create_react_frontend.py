#!/usr/bin/env python3
"""
WS6-01: Create World-Class React Frontend Structure
Generates all necessary files for a production-grade React app
"""

import os
import json
from pathlib import Path

def create_directory_structure():
    """Create the full React app directory structure"""

    base = Path("frontend_app")

    # Create directories
    dirs = [
        base,
        base / "app",
        base / "app" / "assistant",
        base / "components",
        base / "components" / "ui",
        base / "components" / "charts",
        base / "lib",
        base / "public",
    ]

    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created: {dir_path}")

    return base

def create_package_json(base):
    """Create package.json"""
    package_json = {
        "name": "cfo-platform-frontend",
        "version": "1.0.0",
        "private": True,
        "scripts": {
            "dev": "next dev",
            "build": "next build",
            "start": "next start",
            "lint": "next lint"
        },
        "dependencies": {
            "next": "14.1.0",
            "react": "^18.2.0",
            "react-dom": "^18.2.0",
            "recharts": "^2.10.0",
            "axios": "^1.6.5",
            "framer-motion": "^10.18.0",
            "lucide-react": "^0.312.0",
            "date-fns": "^3.3.0",
            "clsx": "^2.1.0",
            "tailwind-merge": "^2.2.0"
        },
        "devDependencies": {
            "@types/node": "^20",
            "@types/react": "^18",
            "@types/react-dom": "^18",
            "typescript": "^5",
            "tailwindcss": "^3.4.0",
            "postcss": "^8",
            "autoprefixer": "^10.0.1",
            "eslint": "^8",
            "eslint-config-next": "14.1.0"
        }
    }

    with open(base / "package.json", "w") as f:
        json.dump(package_json, f, indent=2)

    print("✓ Created: package.json")

def create_typescript_config(base):
    """Create tsconfig.json"""
    tsconfig = {
        "compilerOptions": {
            "target": "ES2017",
            "lib": ["dom", "dom.iterable", "esnext"],
            "allowJs": True,
            "skipLibCheck": True,
            "strict": True,
            "noEmit": True,
            "esModuleInterop": True,
            "module": "esnext",
            "moduleResolution": "bundler",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "jsx": "preserve",
            "incremental": True,
            "plugins": [{"name": "next"}],
            "paths": {"@/*": ["./*"]}
        },
        "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
        "exclude": ["node_modules"]
    }

    with open(base / "tsconfig.json", "w") as f:
        json.dump(tsconfig, f, indent=2)

    print("✓ Created: tsconfig.json")

def create_tailwind_config(base):
    """Create tailwind.config.ts"""
    content = '''import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f4ff',
          100: '#e0e7ff',
          200: '#c7d2fe',
          500: '#3b82f6',
          700: '#1e40af',
          900: '#0c1e3d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}

export default config
'''

    with open(base / "tailwind.config.ts", "w") as f:
        f.write(content)

    print("✓ Created: tailwind.config.ts")

def create_next_config(base):
    """Create next.config.js"""
    content = '''/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
}

module.exports = nextConfig
'''

    with open(base / "next.config.js", "w") as f:
        f.write(content)

    print("✓ Created: next.config.js")

def create_postcss_config(base):
    """Create postcss.config.js"""
    content = '''module.exports = {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
'''

    with open(base / "postcss.config.js", "w") as f:
        f.write(content)

    print("✓ Created: postcss.config.js")

def create_globals_css(base):
    """Create app/globals.css"""
    content = '''@tailwind base;
@tailwind components;
@tailwind utilities;

:root {
  --foreground-rgb: 0, 0, 0;
  --background-start-rgb: 214, 219, 220;
  --background-end-rgb: 255, 255, 255;
}

body {
  color: rgb(var(--foreground-rgb));
  background: linear-gradient(
      to bottom,
      transparent,
      rgb(var(--background-end-rgb))
    )
    rgb(var(--background-start-rgb));
}
'''

    with open(base / "app" / "globals.css", "w") as f:
        f.write(content)

    print("✓ Created: app/globals.css")

def create_layout(base):
    """Create app/layout.tsx"""
    content = '''import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Databricks CFO Platform',
  description: 'AI-Powered Financial Management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
'''

    with open(base / "app" / "layout.tsx", "w") as f:
        f.write(content)

    print("✓ Created: app/layout.tsx")

def create_main_page(base):
    """Create app/page.tsx"""
    content = ''''use client'

import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, Activity, Shield } from 'lucide-react'

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-md sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">
                CFO Platform
              </h1>
              <p className="text-sm text-slate-600">
                Databricks Financial Services
              </p>
            </div>

            <div className="flex items-center gap-4 text-sm text-slate-600">
              <span>Last updated: {new Date().toLocaleTimeString()}</span>
              <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-green-600 font-medium">Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-6 py-8">

        {/* KPI Cards Row */}
        <div className="grid grid-cols-4 gap-6 mb-8">
          <MetricCard
            title="Total Assets"
            value="$45.0B"
            change="+2.1%"
            trend="up"
          />
          <MetricCard
            title="Total Deposits"
            value="$22.0B"
            change="+1.8%"
            trend="up"
          />
          <MetricCard
            title="Net Interest Margin"
            value="2.69%"
            change="-12 bps"
            trend="down"
          />
          <MetricCard
            title="LCR"
            value="104.9%"
            change="Compliant"
            trend="neutral"
          />
        </div>

        {/* Placeholder for charts */}
        <div className="bg-white rounded-lg shadow p-8 text-center text-slate-600">
          <p>Charts and visualizations will render here</p>
          <p className="text-sm mt-2">Connect to FastAPI backend at /api/data/summary</p>
        </div>
      </main>
    </div>
  )
}

function MetricCard({ title, value, change, trend }: {
  title: string
  value: string
  change: string
  trend: 'up' | 'down' | 'neutral'
}) {
  const trendColors = {
    up: 'text-green-600 bg-green-50',
    down: 'text-red-600 bg-red-50',
    neutral: 'text-slate-600 bg-slate-50'
  }

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-4">
        <div className={`p-2 rounded-lg ${trendColors[trend]}`}>
          {trend === 'up' && <TrendingUp className="h-5 w-5" />}
          {trend === 'down' && <TrendingDown className="h-5 w-5" />}
          {trend === 'neutral' && <Shield className="h-5 w-5" />}
        </div>
        <div className={`text-xs font-medium px-2 py-1 rounded ${trendColors[trend]}`}>
          {change}
        </div>
      </div>

      <div>
        <p className="text-sm text-slate-600 mb-1">{title}</p>
        <p className="text-3xl font-bold text-slate-900">{value}</p>
      </div>
    </div>
  )
}
'''

    with open(base / "app" / "page.tsx", "w") as f:
        f.write(content)

    print("✓ Created: app/page.tsx")

def create_readme(base):
    """Create README"""
    content = '''# Databricks CFO Platform - React Frontend

World-class React + TypeScript frontend for CFO banking demo.

## Setup

```bash
npm install
npm run dev
```

Visit http://localhost:3000

## Build for Production

```bash
npm run build
```

Static files will be in `out/` directory.

## Integration with FastAPI

The FastAPI backend should serve these static files and provide API endpoints at:
- /api/chat - Agent chat endpoint
- /api/data/summary - Portfolio summary
- /api/data/yield-curve - Treasury yields
- /api/data/lcr - LCR calculation

## Tech Stack

- Next.js 14 (App Router)
- TypeScript
- Tailwind CSS
- Recharts (charts)
- Framer Motion (animations)
- Lucide React (icons)
'''

    with open(base / "README.md", "w") as f:
        f.write(content)

    print("✓ Created: README.md")

def main():
    print("="*60)
    print("WS6-01: Creating React Frontend Structure")
    print("="*60)
    print()

    # Create directory structure
    base = create_directory_structure()
    print()

    # Create configuration files
    create_package_json(base)
    create_typescript_config(base)
    create_tailwind_config(base)
    create_next_config(base)
    create_postcss_config(base)
    print()

    # Create app files
    create_globals_css(base)
    create_layout(base)
    create_main_page(base)
    create_readme(base)
    print()

    print("="*60)
    print("✅ React Frontend Structure Created Successfully!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. cd frontend_app")
    print("2. npm install")
    print("3. npm run dev")
    print()
    print("For production build:")
    print("  npm run build")
    print("  # Static files will be in out/ directory")
    print()

if __name__ == "__main__":
    main()
