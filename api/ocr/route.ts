// OCR Processing API Route - Next.js 14 App Router
// REST API for OCR operations

import { NextRequest, NextResponse } from 'next/server'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const {
      expense_id,
      receipt_url,
      use_llm_postprocessing = false,
      tenant_id,
      workspace_id,
    } = body

    if (!expense_id || !receipt_url || !tenant_id || !workspace_id) {
      return NextResponse.json(
        { error: 'Missing required fields: expense_id, receipt_url, tenant_id, workspace_id' },
        { status: 400 }
      )
    }

    // Call expense-ocr-processor Edge Function
    const ocrResponse = await fetch(
      `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/expense-ocr-processor`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
        },
        body: JSON.stringify({
          expense_id,
          receipt_url,
          use_llm_postprocessing,
          tenant_id,
          workspace_id,
        }),
      }
    )

    const ocrResult = await ocrResponse.json()

    if (!ocrResponse.ok) {
      return NextResponse.json(
        { error: 'OCR processing failed', details: ocrResult },
        { status: 500 }
      )
    }

    return NextResponse.json({ result: ocrResult }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const expense_id = searchParams.get('expense_id')
    const min_confidence = parseFloat(searchParams.get('min_confidence') || '0')
    const max_confidence = parseFloat(searchParams.get('max_confidence') || '1')
    const limit = parseInt(searchParams.get('limit') || '20')

    let query = supabase
      .from('gold_ocr_results')
      .select('*')
      .gte('confidence', min_confidence)
      .lte('confidence', max_confidence)
      .order('created_at', { ascending: false })
      .limit(limit)

    if (expense_id) {
      query = query.eq('expense_id', expense_id)
    }

    const { data, error } = await query

    if (error) throw error

    // Calculate statistics
    const stats = {
      total_scans: data.length,
      avg_confidence: data.reduce((acc, r) => acc + r.confidence, 0) / data.length,
      high_confidence: data.filter(r => r.confidence >= 0.80).length,
      medium_confidence: data.filter(r => r.confidence >= 0.60 && r.confidence < 0.80).length,
      low_confidence: data.filter(r => r.confidence < 0.60).length,
    }

    return NextResponse.json({ results: data, stats }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
