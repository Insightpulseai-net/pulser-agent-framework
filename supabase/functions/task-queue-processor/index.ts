// Task Queue Processor - Supabase Edge Function
// Processes tasks from scout.task_queue with automatic retry logic

import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TaskQueueRow {
  id: string
  kind: string
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
  priority: number
  payload: Record<string, any>
  attempts: number
  max_attempts: number
}

serve(async (req) => {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Initialize Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // Fetch pending tasks with priority ordering
    const { data: tasks, error: fetchError } = await supabaseClient
      .from('task_queue')
      .select('*')
      .eq('status', 'pending')
      .order('priority', { ascending: false })
      .order('created_at', { ascending: true })
      .limit(10)

    if (fetchError) throw fetchError

    const results = []

    for (const task of tasks as TaskQueueRow[]) {
      try {
        // Update status to processing
        await supabaseClient
          .from('task_queue')
          .update({ status: 'processing', updated_at: new Date().toISOString() })
          .eq('id', task.id)

        // Route to appropriate processor
        const result = await processTask(task)

        // Mark as completed
        await supabaseClient
          .from('task_queue')
          .update({
            status: 'completed',
            result: result,
            updated_at: new Date().toISOString(),
          })
          .eq('id', task.id)

        results.push({ task_id: task.id, status: 'completed' })
      } catch (error) {
        // Increment attempts and handle retry logic
        const newAttempts = task.attempts + 1
        const isFailed = newAttempts >= task.max_attempts

        await supabaseClient
          .from('task_queue')
          .update({
            status: isFailed ? 'failed' : 'pending',
            attempts: newAttempts,
            error_message: error.message,
            next_attempt_at: isFailed
              ? null
              : new Date(Date.now() + 60000 * Math.pow(2, newAttempts)).toISOString(), // Exponential backoff
            updated_at: new Date().toISOString(),
          })
          .eq('id', task.id)

        results.push({
          task_id: task.id,
          status: isFailed ? 'failed' : 'retry_scheduled',
          error: error.message,
        })
      }
    }

    return new Response(JSON.stringify({ processed: results.length, results }), {
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

async function processTask(task: TaskQueueRow): Promise<Record<string, any>> {
  // Task routing logic based on kind
  switch (task.kind) {
    case 'BIR_FORM_FILING':
      return await processBIRFiling(task.payload)
    case 'EXPENSE_OCR_PROCESS':
      return await processExpenseOCR(task.payload)
    case 'BIR_DEADLINE_CHECK':
      return await processBIRDeadlineCheck(task.payload)
    case 'BIR_TASK_CREATE':
      return await processBIRTaskCreate(task.payload)
    default:
      throw new Error(`Unknown task kind: ${task.kind}`)
  }
}

async function processBIRFiling(payload: Record<string, any>): Promise<Record<string, any>> {
  // Mock BIR filing processing
  // In production, integrate with actual BIR eFPS/eBIR API
  console.log('Processing BIR filing:', payload)

  return {
    status: 'filed',
    confirmation_number: `BIR-${Date.now()}`,
    filed_at: new Date().toISOString(),
  }
}

async function processExpenseOCR(payload: Record<string, any>): Promise<Record<string, any>> {
  // Mock OCR processing
  // In production, call PaddleOCR-VL service
  console.log('Processing Expense OCR:', payload)

  return {
    status: 'processed',
    confidence: 0.92,
    vendor_name: 'Sample Vendor',
    amount: 1500.00,
  }
}

async function processBIRDeadlineCheck(payload: Record<string, any>): Promise<Record<string, any>> {
  // Mock deadline check
  console.log('Processing BIR deadline check:', payload)

  return {
    status: 'checked',
    forms_due: 3,
    urgent_count: 1,
  }
}

async function processBIRTaskCreate(payload: Record<string, any>): Promise<Record<string, any>> {
  // Mock BIR task creation
  console.log('Processing BIR task creation:', payload)

  return {
    status: 'created',
    tasks_created: payload.tasks?.length || 0,
  }
}
