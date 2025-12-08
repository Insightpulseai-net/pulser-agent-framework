import { createClient as createSupabaseClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const createClient = () => {
  return createSupabaseClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      persistSession: true,
      autoRefreshToken: true,
    },
  })
}

export type Tables<T extends keyof Database['public']['Tables']> = Database['public']['Tables'][T]['Row']

export interface Database {
  public: {
    Tables: {
      tables: {
        Row: {
          id: string
          schema_name: string
          table_name: string
          description: string | null
          owner: string | null
          row_count: number | null
          size_bytes: number | null
          last_updated: string | null
          dq_score: number | null
          slo_freshness_hours: number | null
          slo_completeness_pct: number | null
        }
      }
      pipelines: {
        Row: {
          id: string
          name: string
          description: string | null
          definition: any
          schedule: string | null
          owner: string | null
          domain: string | null
          enabled: boolean
          n8n_webhook_url: string | null
          created_at: string
          updated_at: string
        }
      }
      agents: {
        Row: {
          id: string
          name: string
          description: string | null
          tools: any
          model: string
          system_prompt: string | null
          temperature: number
          max_tokens: number
          budget_usd: number
          created_by: string | null
          created_at: string
          updated_at: string
        }
      }
      agent_runs: {
        Row: {
          id: string
          agent_id: string
          status: string
          input_prompt: string
          output: string | null
          tokens_used: number | null
          cost_usd: number | null
          model: string | null
          trace_url: string | null
          started_at: string
          completed_at: string | null
          error_message: string | null
        }
      }
      job_runs: {
        Row: {
          id: string
          pipeline_id: string
          status: string
          started_at: string
          completed_at: string | null
          logs: string | null
          rows_processed: number | null
          error_message: string | null
        }
      }
    }
  }
}
