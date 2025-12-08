// BIR Forms API Route - Next.js 14 App Router
// REST API for BIR form operations

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
    const form_type = searchParams.get('form_type')
    const agency = searchParams.get('agency')
    const employee = searchParams.get('employee')
    const period = searchParams.get('period')

    let query = supabase
      .from('silver_bir_forms')
      .select('*')
      .order('filing_deadline', { ascending: true })

    if (status) {
      query = query.eq('status', status)
    }

    if (form_type) {
      query = query.eq('form_type', form_type)
    }

    if (agency) {
      query = query.eq('agency_name', agency)
    }

    if (employee) {
      query = query.eq('employee_name', employee)
    }

    if (period) {
      query = query.like('filing_period', `${period}%`)
    }

    const { data, error } = await query

    if (error) throw error

    return NextResponse.json({ forms: data, count: data.length }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const {
      form_type,
      filing_period,
      filing_deadline,
      agency_name,
      employee_name,
      metadata = {},
    } = body

    if (!form_type || !filing_period || !filing_deadline || !agency_name || !employee_name) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Validate using bir-form-validator Edge Function
    const validationResponse = await fetch(
      `${process.env.NEXT_PUBLIC_SUPABASE_URL}/functions/v1/bir-form-validator`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${process.env.SUPABASE_SERVICE_ROLE_KEY}`,
        },
        body: JSON.stringify({
          form_type,
          filing_period,
          filing_deadline,
          agency_name,
          employee_name,
          metadata,
        }),
      }
    )

    const validation = await validationResponse.json()

    if (!validation.is_valid) {
      return NextResponse.json(
        { error: 'Validation failed', errors: validation.errors },
        { status: 400 }
      )
    }

    // Create BIR form
    const { data, error } = await supabase
      .from('silver_bir_forms')
      .insert({
        form_type,
        filing_period,
        filing_deadline,
        agency_name,
        employee_name,
        status: 'not_started',
        metadata: { ...metadata, ...validation.form_metadata },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      })
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ form: data, validation }, { status: 201 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, status, metadata } = body

    if (!id) {
      return NextResponse.json({ error: 'Missing required field: id' }, { status: 400 })
    }

    const updates: any = {
      updated_at: new Date().toISOString(),
    }

    if (status) updates.status = status
    if (metadata) updates.metadata = metadata

    const { data, error } = await supabase
      .from('silver_bir_forms')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) throw error

    return NextResponse.json({ form: data }, { status: 200 })
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }
}
