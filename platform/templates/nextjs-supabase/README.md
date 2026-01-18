# Next.js + Supabase Golden Template

A production-ready Next.js application with Supabase backend.

## Stack

- **Framework**: Next.js 16 + React 19
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS 4.x + shadcn/ui
- **Backend**: Supabase (PostgreSQL, Auth, Storage, Edge Functions)
- **Deployment**: Vercel / DigitalOcean App Platform
- **CI/CD**: GitHub Actions

## Quick Start

```bash
# Clone template
npx degit platform/templates/nextjs-supabase my-app
cd my-app

# Install dependencies
npm install

# Set up environment
cp .env.example .env.local
# Edit .env.local with your Supabase credentials

# Run development server
npm run dev
```

## Project Structure

```
├── app/                    # Next.js App Router
│   ├── (auth)/              # Auth-required routes
│   ├── (public)/            # Public routes
│   ├── api/                 # API routes
│   └── layout.tsx           # Root layout
├── components/             # React components
│   ├── ui/                  # shadcn/ui components
│   └── features/            # Feature components
├── lib/                    # Utilities
│   ├── supabase/            # Supabase client
│   ├── hooks/               # Custom hooks
│   └── utils/               # Helper functions
├── supabase/               # Supabase config
│   ├── migrations/          # Database migrations
│   ├── functions/           # Edge Functions
│   └── seed.sql             # Seed data
├── tests/                  # Test files
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # Playwright E2E tests
└── .github/workflows/      # CI/CD
    ├── ci.yml               # Lint, test, build
    ├── preview.yml          # Preview deployments
    └── deploy.yml           # Production deploy
```

## Environment Variables

```bash
# .env.local
NEXT_PUBLIC_SUPABASE_URL=https://xxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=xxx
SUPABASE_SERVICE_ROLE_KEY=xxx  # Server-side only
```

## Available Scripts

```bash
npm run dev          # Start dev server
npm run build        # Production build
npm run start        # Start production server
npm run lint         # Run ESLint
npm run test         # Run unit tests
npm run test:e2e     # Run E2E tests
npm run db:migrate   # Run migrations
npm run db:seed      # Seed database
npm run db:reset     # Reset database
```

## Database Migrations

```bash
# Create new migration
supabase migration new my_migration

# Apply migrations locally
supabase db push

# Apply to production (via CI)
# Migrations auto-apply on deploy
```

## Authentication

Pre-configured auth flows:
- Email/password signup & login
- Magic link authentication
- OAuth providers (Google, GitHub)
- Session management with middleware

## RLS Policies

All tables have Row Level Security enabled by default. Example:

```sql
-- users can only see their own data
CREATE POLICY "Users can view own data"
ON public.profiles
FOR SELECT
USING (auth.uid() = user_id);
```

## Testing

```bash
# Unit tests (Vitest)
npm run test

# E2E tests (Playwright)
npm run test:e2e

# Coverage report
npm run test:coverage
```

## Deployment

### Vercel (Recommended)

```bash
vercel deploy --prod
```

### DigitalOcean

```bash
doctl apps create --spec .do/app.yaml
```

## Observability

- **Logs**: Console + Vercel/DO logs
- **Metrics**: Web Vitals + custom metrics
- **Errors**: Sentry integration ready

## Security Checklist

- [x] RLS enabled on all tables
- [x] Environment variables secured
- [x] CORS configured
- [x] Rate limiting on API routes
- [x] Input validation with Zod
- [x] XSS protection headers
- [x] CSRF protection

## Customization

1. Update `tailwind.config.ts` for branding
2. Modify `app/layout.tsx` for global layout
3. Add components to `components/features/`
4. Create API routes in `app/api/`

## Support

Questions? Ask in `#platform-paved-road`
