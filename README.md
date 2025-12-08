# Finance SSC Dashboard - M365 Copilot-Style UI

Multi-agency Finance Shared Services Center dashboard built with Next.js 14, React, Tailwind CSS, and Microsoft Fluent UI design patterns.

## Features

- **Task Queue Monitor**: Real-time task processing status with automatic retry logic
- **BIR Status Dashboard**: Multi-agency BIR filing compliance tracking with 3-level approval workflow
- **OCR Confidence Metrics**: PaddleOCR-VL-900M accuracy monitoring with data quality validation

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **UI**: React 18, Tailwind CSS, Heroicons
- **Backend**: Supabase PostgreSQL (xkxyvboeubffxxbebsll)
- **Charts**: Recharts
- **Real-time**: Supabase Realtime subscriptions
- **Design**: Microsoft Fluent UI patterns

## Setup

1. Install dependencies: `npm install`
2. Copy `.env.example` to `.env.local` and add Supabase credentials
3. Run dev server: `npm run dev`
4. Open http://localhost:3000

## Pages

- `/` - Home dashboard with stats and agency coverage
- `/dashboard/task-queue` - Real-time task monitoring
- `/dashboard/bir-status` - BIR compliance tracking
- `/dashboard/ocr-confidence` - OCR accuracy metrics

## Deployment

Deploy to Vercel: `vercel --prod`

## License

AGPL-3.0 (OCA-compliant)
