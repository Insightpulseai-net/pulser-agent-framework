# Supabase Edge Function Golden Template

A production-ready Supabase Edge Function with testing and secrets management.

## Stack

- **Runtime**: Deno
- **Language**: TypeScript
- **Platform**: Supabase Edge Functions
- **Testing**: Deno test
- **CI/CD**: GitHub Actions

## Quick Start

```bash
# Create new function from template
supabase functions new my-function

# Copy template files
cp -r platform/templates/edge-function/* supabase/functions/my-function/

# Set up secrets
supabase secrets set MY_SECRET=xxx

# Serve locally
supabase functions serve my-function --env-file .env.local

# Test
curl -i --request POST 'http://localhost:54321/functions/v1/my-function' \
  --header 'Authorization: Bearer YOUR_ANON_KEY' \
  --header 'Content-Type: application/json' \
  --data '{"name":"World"}'
```

## Project Structure

```
supabase/functions/my-function/
├── index.ts           # Main function entry
├── handler.ts         # Request handler
├── types.ts           # Type definitions
├── utils.ts           # Utility functions
├── _shared/           # Shared code across functions
│   ├── cors.ts         # CORS headers
│   ├── response.ts     # Response helpers
│   └── auth.ts         # Auth utilities
├── tests/
│   └── handler.test.ts # Unit tests
└── deno.json          # Deno configuration
```

## Function Template

```typescript
// index.ts
import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { handler } from "./handler.ts";
import { corsHeaders } from "./_shared/cors.ts";

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    return await handler(req);
  } catch (error) {
    console.error("Function error:", error);
    return new Response(
      JSON.stringify({ error: "Internal server error" }),
      {
        status: 500,
        headers: { ...corsHeaders, "Content-Type": "application/json" },
      }
    );
  }
});
```

```typescript
// handler.ts
import { corsHeaders } from "./_shared/cors.ts";
import { createResponse, errorResponse } from "./_shared/response.ts";
import type { RequestPayload, ResponsePayload } from "./types.ts";

export async function handler(req: Request): Promise<Response> {
  // Validate method
  if (req.method !== "POST") {
    return errorResponse(405, "Method not allowed");
  }

  // Parse and validate input
  const payload: RequestPayload = await req.json();

  if (!payload.name) {
    return errorResponse(400, "Missing required field: name");
  }

  // Business logic
  const result: ResponsePayload = {
    message: `Hello, ${payload.name}!`,
    timestamp: new Date().toISOString(),
  };

  return createResponse(result);
}
```

## Types

```typescript
// types.ts
export interface RequestPayload {
  name: string;
  options?: {
    uppercase?: boolean;
  };
}

export interface ResponsePayload {
  message: string;
  timestamp: string;
}
```

## Shared Utilities

```typescript
// _shared/cors.ts
export const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

// _shared/response.ts
import { corsHeaders } from "./cors.ts";

export function createResponse<T>(data: T, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
}

export function errorResponse(status: number, message: string): Response {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: {
      ...corsHeaders,
      "Content-Type": "application/json",
    },
  });
}

// _shared/auth.ts
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

export function getSupabaseClient(req: Request) {
  const authHeader = req.headers.get("Authorization")!;
  const supabaseUrl = Deno.env.get("SUPABASE_URL")!;
  const supabaseKey = Deno.env.get("SUPABASE_ANON_KEY")!;

  return createClient(supabaseUrl, supabaseKey, {
    global: {
      headers: { Authorization: authHeader },
    },
  });
}

export async function getUser(req: Request) {
  const supabase = getSupabaseClient(req);
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    throw new Error("Unauthorized");
  }

  return user;
}
```

## Testing

```typescript
// tests/handler.test.ts
import { assertEquals } from "https://deno.land/std@0.168.0/testing/asserts.ts";
import { handler } from "../handler.ts";

Deno.test("handler returns greeting", async () => {
  const req = new Request("http://localhost/my-function", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name: "World" }),
  });

  const res = await handler(req);
  const body = await res.json();

  assertEquals(res.status, 200);
  assertEquals(body.message, "Hello, World!");
});

Deno.test("handler rejects missing name", async () => {
  const req = new Request("http://localhost/my-function", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({}),
  });

  const res = await handler(req);

  assertEquals(res.status, 400);
});
```

Run tests:
```bash
deno test --allow-env tests/
```

## Secrets Management

```bash
# Set secrets
supabase secrets set API_KEY=xxx
supabase secrets set WEBHOOK_URL=https://example.com/webhook

# List secrets
supabase secrets list

# Access in code
const apiKey = Deno.env.get("API_KEY");
```

## Local Development

```bash
# Start Supabase locally
supabase start

# Serve function with hot reload
supabase functions serve my-function --env-file .env.local

# Test locally
curl -i --request POST 'http://localhost:54321/functions/v1/my-function' \
  --header 'Authorization: Bearer YOUR_ANON_KEY' \
  --header 'Content-Type: application/json' \
  --data '{"name":"World"}'
```

## Deployment

```bash
# Deploy single function
supabase functions deploy my-function

# Deploy all functions
supabase functions deploy

# Deploy via CI (GitHub Actions)
# See .github/workflows/deploy-functions.yml
```

## CI/CD

```yaml
# .github/workflows/deploy-functions.yml
name: Deploy Edge Functions

on:
  push:
    branches: [main]
    paths:
      - 'supabase/functions/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: supabase/setup-cli@v1
        with:
          version: latest

      - run: supabase functions deploy --project-ref ${{ secrets.SUPABASE_PROJECT_REF }}
        env:
          SUPABASE_ACCESS_TOKEN: ${{ secrets.SUPABASE_ACCESS_TOKEN }}
```

## Performance Tips

1. **Cold starts**: Keep functions small and avoid heavy imports
2. **Reuse connections**: Store clients outside handler
3. **Caching**: Use in-memory caching for repeated lookups
4. **Timeouts**: Functions have 60s timeout by default

## Security Checklist

- [x] Validate all inputs
- [x] Use Supabase Auth for authentication
- [x] Never expose service role key
- [x] Use environment variables for secrets
- [x] Add rate limiting for public endpoints
- [x] Log security-relevant events

## Limitations

- 60 second execution timeout
- 150MB memory limit
- No persistent storage (use Supabase DB)
- Limited Deno APIs available

## Support

Questions? Ask in `#platform-paved-road`
