# Supabase Integration Guide

> **Leveraging Supabase for Docs2Code Pipeline**

## Overview

This guide shows how to integrate Supabase with the InsightPulseAI Docs2Code pipeline for:
- Database schema extraction → Documentation
- Real-time sync between Odoo and Supabase
- PostgreSQL Connector for Google Sheets integration
- Authentication for generated applications

---

## Supabase Products Used

| Product | Use Case |
|---------|----------|
| **Database** | PostgreSQL for schema extraction, real-time sync |
| **Auth** | Authentication for generated apps |
| **Storage** | Document storage, generated file hosting |
| **Realtime** | Live updates between Odoo ↔ Supabase |
| **Edge Functions** | Serverless code generation triggers |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    DOCS2CODE + SUPABASE ARCHITECTURE                │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────┐    ┌──────────────────┐    ┌─────────────────────────┐
│ Google Docs  │───▶│ Docs2Code        │───▶│ Generated Code          │
│ (Source)     │    │ Pipeline         │    │ (Odoo modules)          │
└──────────────┘    └──────────────────┘    └─────────────────────────┘
                           │                          │
                           ▼                          ▼
                    ┌──────────────────┐    ┌─────────────────────────┐
                    │ Supabase DB      │◀───│ Odoo 18 CE              │
                    │ (PostgreSQL)     │    │ (ERP)                   │
                    └──────────────────┘    └─────────────────────────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │ Google     │  │ Realtime   │  │ Edge       │
    │ Sheets     │  │ Sync       │  │ Functions  │
    │ (Reports)  │  │ (Live)     │  │ (Triggers) │
    └────────────┘  └────────────┘  └────────────┘
```

---

## Setup Guide

### 1. Environment Configuration

Create `.env.local` (never commit this file):

```bash
# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL="https://YOUR_PROJECT.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="your-anon-key"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"

# Database URLs
DATABASE_URL="postgres://postgres:PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"
DIRECT_URL="postgres://postgres:PASSWORD@db.YOUR_PROJECT.supabase.co:5432/postgres"

# For connection pooling (recommended for serverless)
POSTGRES_PRISMA_URL="postgres://postgres:PASSWORD@YOUR_PROJECT.pooler.supabase.com:6543/postgres?pgbouncer=true"
```

### 2. Database Schema for Docs2Code

```sql
-- Create schema for docs2code tracking
CREATE SCHEMA IF NOT EXISTS docs2code;

-- Document sources
CREATE TABLE docs2code.sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    google_doc_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    last_synced_at TIMESTAMPTZ,
    revision_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generated modules
CREATE TABLE docs2code.generated_modules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_id UUID REFERENCES docs2code.sources(id),
    module_name TEXT NOT NULL,
    framework TEXT NOT NULL, -- 'odoo', 'fastapi', 'react'
    version TEXT NOT NULL,
    file_count INTEGER,
    github_path TEXT,
    github_commit_sha TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Generation logs
CREATE TABLE docs2code.generation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    module_id UUID REFERENCES docs2code.generated_modules(id),
    status TEXT NOT NULL, -- 'started', 'completed', 'failed'
    message TEXT,
    duration_ms INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE docs2code.sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs2code.generated_modules ENABLE ROW LEVEL SECURITY;
ALTER TABLE docs2code.generation_logs ENABLE ROW LEVEL SECURITY;

-- Policies (adjust based on your auth requirements)
CREATE POLICY "Allow authenticated read" ON docs2code.sources
    FOR SELECT TO authenticated USING (true);

CREATE POLICY "Allow service role write" ON docs2code.sources
    FOR ALL TO service_role USING (true);
```

### 3. Google Sheets Integration via PostgreSQL Connector

#### Connect Google Sheets to Supabase

1. Open Google Sheets
2. **Extensions** → **SyncWith** → **Connect**
3. Add PostgreSQL connection:
   - **Host**: `db.YOUR_PROJECT.supabase.co`
   - **Port**: `5432`
   - **Database**: `postgres`
   - **User**: `postgres`
   - **Password**: Your Supabase database password

#### Useful Queries for Documentation

**Extract table schemas:**
```sql
SELECT
    c.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable,
    c.column_default,
    pgd.description AS column_comment
FROM information_schema.columns c
LEFT JOIN pg_catalog.pg_statio_all_tables st
    ON c.table_schema = st.schemaname AND c.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
    ON pgd.objoid = st.relid AND pgd.objsubid = c.ordinal_position
WHERE c.table_schema = 'public'
ORDER BY c.table_name, c.ordinal_position;
```

**Extract foreign key relationships:**
```sql
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';
```

**Track generation history:**
```sql
SELECT
    s.title AS source_document,
    m.module_name,
    m.framework,
    m.file_count,
    l.status,
    l.duration_ms,
    l.created_at
FROM docs2code.generation_logs l
JOIN docs2code.generated_modules m ON l.module_id = m.id
JOIN docs2code.sources s ON m.source_id = s.id
ORDER BY l.created_at DESC
LIMIT 100;
```

---

## Supabase Edge Function for Docs2Code Trigger

### Create Edge Function

```typescript
// supabase/functions/docs2code-trigger/index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    const { google_doc_id, output_path } = await req.json()

    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Log the trigger
    const { data: source, error: sourceError } = await supabaseClient
      .from('docs2code.sources')
      .upsert({
        google_doc_id,
        last_synced_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (sourceError) throw sourceError

    // Trigger GitHub Actions workflow via API
    const githubResponse = await fetch(
      `https://api.github.com/repos/Insightpulseai-net/pulser-agent-framework/actions/workflows/docs-to-code.yml/dispatches`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${Deno.env.get('GITHUB_TOKEN')}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ref: 'main',
          inputs: {
            google_doc_id,
            output_path: output_path || 'generated/odoo/',
          },
        }),
      }
    )

    if (!githubResponse.ok) {
      throw new Error(`GitHub API error: ${githubResponse.status}`)
    }

    return new Response(
      JSON.stringify({
        success: true,
        source_id: source.id,
        message: 'Docs2Code pipeline triggered',
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )

  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )
  }
})
```

### Deploy Edge Function

```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link project
supabase link --project-ref YOUR_PROJECT_REF

# Deploy function
supabase functions deploy docs2code-trigger

# Set secrets
supabase secrets set GITHUB_TOKEN=your_github_token
```

---

## Realtime Sync: Odoo ↔ Supabase

### Enable Realtime on Tables

```sql
-- Enable realtime for specific tables
ALTER PUBLICATION supabase_realtime ADD TABLE docs2code.sources;
ALTER PUBLICATION supabase_realtime ADD TABLE docs2code.generated_modules;
ALTER PUBLICATION supabase_realtime ADD TABLE docs2code.generation_logs;
```

### JavaScript Client for Realtime Updates

```typescript
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Subscribe to generation updates
const subscription = supabase
  .channel('docs2code-updates')
  .on(
    'postgres_changes',
    {
      event: '*',
      schema: 'docs2code',
      table: 'generation_logs',
    },
    (payload) => {
      console.log('Generation update:', payload)

      if (payload.new.status === 'completed') {
        // Notify user, refresh UI, etc.
        showNotification(`Module generated: ${payload.new.module_name}`)
      }
    }
  )
  .subscribe()
```

---

## Authentication for Generated Apps

### Supabase Auth Setup

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

// Sign in with email
export async function signInWithEmail(email: string, password: string) {
  const { data, error } = await supabase.auth.signInWithPassword({
    email,
    password,
  })
  return { data, error }
}

// Sign in with OAuth (Google, GitHub, etc.)
export async function signInWithOAuth(provider: 'google' | 'github') {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })
  return { data, error }
}
```

### Protect Generated Module Access

```sql
-- Row Level Security for module access
CREATE POLICY "Users can view their organization's modules"
ON docs2code.generated_modules
FOR SELECT
USING (
  auth.uid() IN (
    SELECT user_id FROM organization_members
    WHERE organization_id = generated_modules.organization_id
  )
);
```

---

## Storage for Generated Files

### Upload Generated Code to Supabase Storage

```typescript
// Upload generated module to storage
async function uploadGeneratedModule(
  moduleFiles: Record<string, string>,
  moduleName: string
) {
  const results = []

  for (const [filename, content] of Object.entries(moduleFiles)) {
    const path = `modules/${moduleName}/${filename}`

    const { data, error } = await supabase.storage
      .from('generated-code')
      .upload(path, content, {
        contentType: 'text/plain',
        upsert: true,
      })

    results.push({ path, success: !error, error })
  }

  return results
}

// Get download URL
async function getModuleDownloadUrl(moduleName: string) {
  const { data } = await supabase.storage
    .from('generated-code')
    .createSignedUrl(`modules/${moduleName}/module.zip`, 3600)

  return data?.signedUrl
}
```

### Storage Bucket Configuration

```sql
-- Create storage bucket for generated code
INSERT INTO storage.buckets (id, name, public)
VALUES ('generated-code', 'generated-code', false);

-- Policy: Only authenticated users can download
CREATE POLICY "Authenticated users can download modules"
ON storage.objects
FOR SELECT
TO authenticated
USING (bucket_id = 'generated-code');
```

---

## Complete Integration Flow

```
1. User creates/updates Google Doc
           ↓
2. Docs to Markdown Pro exports to GitHub
           ↓
3. GitHub Actions triggers Supabase Edge Function
           ↓
4. Edge Function:
   ├── Logs source in docs2code.sources
   ├── Triggers Colab notebook (via API)
   └── Updates docs2code.generation_logs
           ↓
5. Colab notebook:
   ├── Fetches Google Doc
   ├── Parses structure
   ├── Generates Odoo module
   └── Pushes to GitHub
           ↓
6. Supabase Realtime:
   ├── Notifies connected clients
   └── Updates dashboard
           ↓
7. Storage:
   ├── Archives generated code
   └── Provides download links
```

---

## Monitoring Dashboard Query

```sql
-- Dashboard overview
SELECT
    (SELECT COUNT(*) FROM docs2code.sources) AS total_sources,
    (SELECT COUNT(*) FROM docs2code.generated_modules) AS total_modules,
    (SELECT COUNT(*) FROM docs2code.generation_logs WHERE status = 'completed') AS successful_generations,
    (SELECT COUNT(*) FROM docs2code.generation_logs WHERE status = 'failed') AS failed_generations,
    (SELECT AVG(duration_ms) FROM docs2code.generation_logs WHERE status = 'completed') AS avg_duration_ms;
```

---

## Security Best Practices

1. **Never commit credentials** - Use `.env.local` and `.gitignore`
2. **Use service role key only server-side** - Never expose in client code
3. **Enable RLS on all tables** - Default deny, explicit allow
4. **Use connection pooling** - Supavisor for serverless
5. **Rotate keys regularly** - Regenerate anon and service keys periodically
6. **Monitor access logs** - Check Supabase dashboard for anomalies

---

## References

- [Supabase Documentation](https://supabase.com/docs)
- [Supabase JavaScript Client](https://supabase.com/docs/reference/javascript)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [PostgreSQL Connector for Sheets](https://workspace.google.com/marketplace/app/syncwith/449644239211)

---

*InsightPulseAI Docs2Code Pipeline - Supabase Integration*
*Last Updated: 2025-12-30*
