// Task Queue API Route - Next.js 14 App Router
// REST API for task queue operations

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const status = searchParams.get('status')
    const kind = searchParams.get('kind')
    const limit = parseInt(searchParams.get('limit') || '20')

    let query = supabase
      .from('task_queue')
      .select('*')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true })
      .limit(limit)

    if (status) {
      query = query.eq('status', status)
    }

    if (kind) {
      query = query.eq('kind', kind)
    }

    const { data, error } = await query

    if (error) throw error

    return NextResponse.json({ tasks: data, count: data.length }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const { kind, payload, priority = 5, max_attempts = 3 } = body

    if (!kind || !payload) {
      return NextResponse.json(
        { error: 'Missing required fields: kind, payload' },
        { status: 400 }
      )
    }

    const { data, error } = await supabase
      .from('task_queue')
      .insert({
        kind,
        status: 'pending',
        priority,
        payload,
        attempts: 0,
        max_attempts,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ task: data }, { status: 201 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, status, result, error_message } = body

    if (!id || !status) {
      return NextResponse.json(
        { error: 'Missing required fields: id, status' },
        { status: 400 }
      )
    }

    const updates: any = {
      status,
      updated_at: new Date().toISOString(),
    }

    if (result) updates.result = result
    if (error_message) updates.error_message = error_message

    const { data, error } = await supabase
      .from('task_queue')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ task: data }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
