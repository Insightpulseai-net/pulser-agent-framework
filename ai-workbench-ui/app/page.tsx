'use client'

import { useEffect, useState } from 'react'
import KPICard from '@/components/KPICard'
import ActivityFeed from '@/components/ActivityFeed'
import { createClient } from '@/lib/supabase/client'

interface KPISummary {
  total_tables: number
  total_pipelines: number
  total_agents: number
  avg_dq_score: number
}

interface Activity {
  id: string
  type: 'pipeline_run' | 'query' | 'agent_execution'
  description: string
  timestamp: string
  status: 'success' | 'failure' | 'running'
}

export default function Home() {
  const [kpis, setKpis] = useState<KPISummary | null>(null)
  const [activities, setActivities] = useState<Activity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      const supabase = createClient()

      // Fetch KPI summary
      const { data: tablesCount } = await supabase
        .from('tables')
        .select('*', { count: 'exact', head: true })

      const { data: pipelinesCount } = await supabase
        .from('pipelines')
        .select('*', { count: 'exact', head: true })

      const { data: agentsCount } = await supabase
        .from('agents')
        .select('*', { count: 'exact', head: true })

      const { data: dqScores } = await supabase
        .from('tables')
        .select('dq_score')
        .not('dq_score', 'is', null)

      const avgDQScore = dqScores && dqScores.length > 0
        ? dqScores.reduce((sum, t) => sum + (t.dq_score || 0), 0) / dqScores.length
        : 0

      setKpis({
        total_tables: tablesCount?.count || 0,
        total_pipelines: pipelinesCount?.count || 0,
        total_agents: agentsCount?.count || 0,
        avg_dq_score: avgDQScore,
      })

      // Fetch recent activities
      const { data: recentRuns } = await supabase
        .from('job_runs')
        .select('id, pipeline_id, status, started_at, pipelines(name)')
        .order('started_at', { ascending: false })
        .limit(10)

      if (recentRuns) {
        const activityData = recentRuns.map((run: any) => ({
          id: run.id,
          type: 'pipeline_run' as const,
          description: `Pipeline "${run.pipelines?.name}" executed`,
          timestamp: run.started_at,
          status: run.status === 'completed' ? 'success' as const :
                  run.status === 'failed' ? 'failure' as const : 'running' as const,
        }))
        setActivities(activityData)
      }

      setLoading(false)
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-lg text-gray-600 dark:text-gray-400">Loading dashboard...</div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Dashboard</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Welcome to InsightPulseAI Workbench
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <KPICard
          title="Total Tables"
          value={kpis?.total_tables || 0}
          trend="+12%"
          icon="📊"
          onClick={() => window.location.href = '/catalog'}
        />
        <KPICard
          title="Pipelines"
          value={kpis?.total_pipelines || 0}
          trend="+5%"
          icon="🔄"
          onClick={() => window.location.href = '/pipelines'}
        />
        <KPICard
          title="AI Agents"
          value={kpis?.total_agents || 0}
          trend="+8%"
          icon="🤖"
          onClick={() => window.location.href = '/genie'}
        />
        <KPICard
          title="Data Quality"
          value={`${Math.round(kpis?.avg_dq_score || 0)}%`}
          trend="+3%"
          icon="✅"
          onClick={() => window.location.href = '/quality'}
        />
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
              Recent Activity
            </h2>
            <ActivityFeed items={activities} />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-white">
            Quick Actions
          </h2>
          <div className="space-y-3">
            <button
              onClick={() => window.location.href = '/pipelines?new=true'}
              className="w-full px-4 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-left flex items-center space-x-3"
            >
              <span>➕</span>
              <span>New Pipeline</span>
            </button>
            <button
              onClick={() => window.location.href = '/sql'}
              className="w-full px-4 py-3 bg-green-500 hover:bg-green-600 text-white rounded-lg text-left flex items-center space-x-3"
            >
              <span>📝</span>
              <span>Run Query</span>
            </button>
            <button
              onClick={() => window.location.href = '/genie'}
              className="w-full px-4 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-lg text-left flex items-center space-x-3"
            >
              <span>🤖</span>
              <span>Ask Genie</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
