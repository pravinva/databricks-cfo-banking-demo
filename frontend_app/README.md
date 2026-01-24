# Databricks CFO Platform - React Frontend

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
