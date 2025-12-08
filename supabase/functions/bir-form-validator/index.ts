// BIR Form Validator - Supabase Edge Function
// Validates BIR form data before filing submission

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface BIRValidationRequest {
  bir_form_id: string
  form_type: string
  filing_period: string
  filing_deadline: string
  agency_name: string
  employee_name: string
  metadata?: Record<string, any>
}

interface ValidationResult {
  is_valid: boolean
  errors: string[]
  warnings: string[]
  form_metadata: Record<string, any>
}

const formTypeConfig = {
  '1601-C': {
    name: 'Monthly Remittance (Compensation)',
    frequency: 'monthly',
    required_fields: ['form_type', 'filing_period', 'filing_deadline', 'agency_name', 'employee_name'],
  },
  '0619-E': {
    name: 'Monthly Remittance (Expanded)',
    frequency: 'monthly',
    required_fields: ['form_type', 'filing_period', 'filing_deadline', 'agency_name', 'employee_name'],
  },
  '2550Q': {
    name: 'Quarterly Income Tax',
    frequency: 'quarterly',
    required_fields: ['form_type', 'filing_period', 'filing_deadline', 'agency_name', 'employee_name'],
  },
  '1702-RT': {
    name: 'Annual Reconciliation',
    frequency: 'annual',
    required_fields: ['form_type', 'filing_period', 'filing_deadline', 'agency_name', 'employee_name'],
  },
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { bir_form_id, form_type, filing_period, filing_deadline, agency_name, employee_name, metadata } =
      await req.json() as BIRValidationRequest

    // Perform validation
    const validation = await validateBIRForm({
      bir_form_id,
      form_type,
      filing_period,
      filing_deadline,
      agency_name,
      employee_name,
      metadata,
    })

    return new Response(JSON.stringify(validation), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: validation.is_valid ? 200 : 400,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})

async function validateBIRForm(request: BIRValidationRequest): Promise<ValidationResult> {
  const errors: string[] = []
  const warnings: string[] = []
  const formMetadata: Record<string, any> = {}

  // 1. Validate form type
  if (!formTypeConfig[request.form_type as keyof typeof formTypeConfig]) {
    errors.push(`Invalid form type: ${request.form_type}`)
  } else {
    const config = formTypeConfig[request.form_type as keyof typeof formTypeConfig]
    formMetadata.form_name = config.name
    formMetadata.frequency = config.frequency

    // 2. Validate required fields
    for (const field of config.required_fields) {
      if (!request[field as keyof BIRValidationRequest]) {
        errors.push(`Missing required field: ${field}`)
      }
    }
  }

  // 3. Validate filing period format
  if (request.filing_period) {
    const periodRegex = /^\d{4}-(0[1-9]|1[0-2])(-Q[1-4])?$/
    if (!periodRegex.test(request.filing_period)) {
      errors.push('Invalid filing period format. Expected: YYYY-MM or YYYY-MM-Q1/Q2/Q3/Q4')
    }

    // Check period matches form frequency
    const config = formTypeConfig[request.form_type as keyof typeof formTypeConfig]
    if (config) {
      if (config.frequency === 'quarterly' && !request.filing_period.includes('-Q')) {
        errors.push('Quarterly form requires period format with quarter (e.g., 2025-12-Q4)')
      }
      if (config.frequency === 'monthly' && request.filing_period.includes('-Q')) {
        errors.push('Monthly form should not include quarter in period')
      }
    }
  }

  // 4. Validate filing deadline
  if (request.filing_deadline) {
    const deadline = new Date(request.filing_deadline)
    const now = new Date()

    if (isNaN(deadline.getTime())) {
      errors.push('Invalid filing deadline format')
    } else {
      // Check if deadline is in the past
      if (deadline < now) {
        warnings.push(`Filing deadline has passed (${deadline.toISOString()}). Form will be marked as late.`)
        formMetadata.late_filing = true
      } else {
        // Check if deadline is within 3 days
        const daysUntilDeadline = (deadline.getTime() - now.getTime()) / (1000 * 60 * 60 * 24)
        if (daysUntilDeadline <= 3) {
          warnings.push(`Filing deadline is in ${Math.ceil(daysUntilDeadline)} days - urgent action required`)
          formMetadata.urgent = true
        }
      }
    }
  }

  // 5. Validate agency name (must be one of the 8 agencies)
  const validAgencies = [
    'TBWA\\Santiago Mangada Puno',
    'TBWA\\SMP',
    'TBWA\\Strategic Data Corp',
    'TBWA\\Chiat\\Day Philippines',
    'TBWA\\Free',
    'TBWA\\Digital Arts Network',
    'Digitas Philippines',
    'C&M Consulting',
  ]

  if (request.agency_name && !validAgencies.includes(request.agency_name)) {
    warnings.push(`Agency name not in standard list: ${request.agency_name}`)
  }

  // 6. Validate employee name (must be one of the 8 employees)
  const validEmployees = ['RIM', 'CKVC', 'BOM', 'JPAL', 'JLI', 'JAP', 'LAS', 'RMQB']
  if (request.employee_name && !validEmployees.includes(request.employee_name)) {
    warnings.push(`Employee name not in standard list: ${request.employee_name}`)
  }

  // Add metadata
  formMetadata.validated_at = new Date().toISOString()
  formMetadata.validation_version = '1.0'

  return {
    is_valid: errors.length === 0,
    errors,
    warnings,
    form_metadata: formMetadata,
  }
}
