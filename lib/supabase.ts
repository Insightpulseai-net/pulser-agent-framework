import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    persistSession: false,
  },
  realtime: {
    params: {
      eventsPerSecond: 10,
    },
  },
})

// Database types (aligned with canonical schema)
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled'
export type BIRStatus = 'not_started' | 'in_progress' | 'submitted' | 'filed' | 'late' | 'overdue' | 'rejected'

export interface TaskQueueRow {
  id: string
  tenant_id: string
  workspace_id: string
  kind: string
  status: TaskStatus
  priority: number
  payload: Record<string, any>
  result?: Record<string, any>
  error_message?: string
  attempts: number
  max_attempts: number
  next_attempt_at?: string
  created_at: string
  updated_at: string
}

export interface BIRFormRow {
  id: string
  tenant_id: string
  workspace_id: string
  form_type: string
  filing_period: string
  filing_deadline: string
  agency_name: string
  employee_name: string
  status: BIRStatus
  filed_date?: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}

export interface ExpenseOCRRow {
  id: string
  tenant_id: string
  workspace_id: string
  expense_id: string
  confidence_score: number
  vendor_name?: string
  amount?: number
  date?: string
  status: string
  metadata: Record<string, any>
  created_at: string
  updated_at: string
}
