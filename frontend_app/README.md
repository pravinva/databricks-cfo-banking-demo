# Databricks CFO Platform - React Frontend

React + TypeScript frontend for **Databricks Apps** (served by the FastAPI backend).

## Setup

```bash
npm install
npm run dev
```

Visit `http://localhost:3000`.

## Build for Databricks Apps (static export)

```bash
npm run build
```

Static files will be in `out/` directory. The backend serves these files from `frontend_app/out/`.

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
