// Expense OCR Processor - Supabase Edge Function
// Processes expense receipts with PaddleOCR-VL and optional LLM post-processing

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface OCRRequest {
  expense_id: string
  receipt_url: string
  use_llm_postprocessing?: boolean
  tenant_id: string
  workspace_id: string
}

interface OCRResult {
  expense_id: string
  confidence: number
  vendor_name: string
  amount: number
  date: string
  category: string
  tax_amount?: number
  extracted_fields: Record<string, any>
  processing_time_ms: number
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const startTime = Date.now()

    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    const { expense_id, receipt_url, use_llm_postprocessing, tenant_id, workspace_id } =
      await req.json() as OCRRequest

    // Step 1: Call PaddleOCR-VL service
    const ocrResponse = await callPaddleOCR(receipt_url)

    // Step 2: Optional LLM post-processing for field extraction
    let extractedFields = ocrResponse.extracted_fields
    if (use_llm_postprocessing && ocrResponse.confidence >= 0.60) {
      extractedFields = await callLLMPostProcessing(ocrResponse.raw_text, ocrResponse.extracted_fields)
    }

    // Step 3: Validate extracted data
    const validation = validateExtractedData(extractedFields)

    // Step 4: Calculate confidence score
    const confidence = calculateConfidence(ocrResponse, validation)

    // Step 5: Store OCR result in Supabase
    const result: OCRResult = {
      expense_id,
      confidence,
      vendor_name: extractedFields.vendor_name || '',
      amount: extractedFields.amount || 0,
      date: extractedFields.date || new Date().toISOString(),
      category: extractedFields.category || 'Uncategorized',
      tax_amount: extractedFields.tax_amount,
      extracted_fields: extractedFields,
      processing_time_ms: Date.now() - startTime,
    }

    // Store in scout.gold_ocr_results
    await supabaseClient
      .from('gold_ocr_results')
      .insert({
        tenant_id,
        workspace_id,
        expense_id,
        confidence: result.confidence,
        vendor_name: result.vendor_name,
        amount: result.amount,
        date: result.date,
        category: result.category,
        extracted_fields: result.extracted_fields,
        processing_time_ms: result.processing_time_ms,
        created_at: new Date().toISOString(),
      })

    // Update expense record with OCR results
    await supabaseClient
      .from('silver_expenses')
      .update({
        ocr_confidence: result.confidence,
        ocr_processed: true,
        vendor_name: result.vendor_name,
        amount: result.amount,
        updated_at: new Date().toISOString(),
      })
      .eq('id', expense_id)

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 200,
    })
  } catch (error) {
    return new Response(JSON.stringify({ error: error.message }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      status: 400,
    })
  }
})

async function callPaddleOCR(receiptUrl: string): Promise<any> {
  // Mock PaddleOCR-VL API call
  // In production: POST to https://ade-ocr-backend-*.ondigitalocean.app/ocr
  console.log('Calling PaddleOCR-VL for:', receiptUrl)

  // Simulate OCR processing
  return {
    confidence: 0.92,
    raw_text: 'Sample receipt text...',
    extracted_fields: {
      vendor_name: 'Sample Vendor Inc.',
      amount: 1500.00,
      date: '2025-12-01',
      tax_amount: 180.00,
      category: 'Office Supplies',
      receipt_number: 'RCT-2025-001',
    },
  }
}

async function callLLMPostProcessing(rawText: string, extractedFields: Record<string, any>): Promise<Record<string, any>> {
  // Mock OpenAI GPT-4o-mini post-processing
  // In production: Call OpenAI API with prompt engineering for field extraction
  console.log('LLM post-processing for fields:', extractedFields)

  // Simulate LLM enhancement
  return {
    ...extractedFields,
    category: 'Office Supplies', // Enhanced category classification
    vendor_confidence: 0.95,
    amount_confidence: 0.98,
    date_confidence: 0.90,
  }
}

function validateExtractedData(fields: Record<string, any>): { is_valid: boolean; errors: string[] } {
  const errors: string[] = []

  if (!fields.vendor_name) errors.push('Missing vendor name')
  if (!fields.amount || fields.amount <= 0) errors.push('Invalid amount')
  if (!fields.date) errors.push('Missing date')

  // Validate date format
  if (fields.date) {
    const dateRegex = /^\d{4}-\d{2}-\d{2}$/
    if (!dateRegex.test(fields.date)) {
      errors.push('Invalid date format (expected YYYY-MM-DD)')
    }
  }

  // Validate amount is numeric
  if (fields.amount && isNaN(fields.amount)) {
    errors.push('Amount must be numeric')
  }

  return {
    is_valid: errors.length === 0,
    errors,
  }
}

function calculateConfidence(ocrResponse: any, validation: any): number {
  let confidence = ocrResponse.confidence

  // Reduce confidence if validation errors exist
  if (!validation.is_valid) {
    confidence = confidence * 0.8 // 20% penalty for validation errors
  }

  // Boost confidence if LLM confirmed fields
  if (ocrResponse.extracted_fields.vendor_confidence) {
    const avgFieldConfidence = (
      (ocrResponse.extracted_fields.vendor_confidence || 0) +
      (ocrResponse.extracted_fields.amount_confidence || 0) +
      (ocrResponse.extracted_fields.date_confidence || 0)
    ) / 3
    confidence = (confidence + avgFieldConfidence) / 2
  }

  return Math.round(confidence * 100) / 100 // Round to 2 decimals
}
