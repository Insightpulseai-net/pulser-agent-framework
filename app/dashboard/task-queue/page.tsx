'use client'

import { useEffect, useState } from 'react'
import { supabase, TaskQueueRow, TaskStatus } from '@/lib/supabase'
import {
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

const statusConfig: Record<TaskStatus, { label: string; className: string; icon: any }> = {
  pending: {
    label: 'Pending',
    className: 'status-neutral',
    icon: ClockIcon,
  },
  processing: {
    label: 'Processing',
    className: 'status-info',
    icon: ArrowPathIcon,
  },
  completed: {
    label: 'Completed',
    className: 'status-success',
    icon: CheckCircleIcon,
  },
  failed: {
    label: 'Failed',
    className: 'status-error',
    icon: XCircleIcon,
  },
  cancelled: {
    label: 'Cancelled',
    className: 'status-warning',
    icon: ExclamationTriangleIcon,
  },
}

export default function TaskQueueDashboard() {
  const [tasks, setTasks] = useState<TaskQueueRow[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    processing: 0,
    completed: 0,
    failed: 0,
  })

  useEffect(() => {
    fetchTasks()
    fetchStats()

    // Subscribe to real-time updates
    const channel = supabase
      .channel('task_queue_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'scout', table: 'task_queue' },
        () => {
          fetchTasks()
          fetchStats()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  async function fetchTasks() {
    const { data, error } = await supabase
      .from('task_queue')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(50)

    if (data) {
      setTasks(data as TaskQueueRow[])
    }
    setLoading(false)
  }

  async function fetchStats() {
    const { data, error } = await supabase
      .from('task_queue')
      .select('status')

    if (data) {
      const stats = {
        total: data.length,
        pending: data.filter((t) => t.status === 'pending').length,
        processing: data.filter((t) => t.status === 'processing').length,
        completed: data.filter((t) => t.status === 'completed').length,
        failed: data.filter((t) => t.status === 'failed').length,
      }
      setStats(stats)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ArrowPathIcon className="h-8 w-8 animate-spin text-brand-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-title-large text-neutral-900 dark:text-neutral-100">
          Task Queue Monitor
        </h1>
        <p className="mt-2 text-body text-neutral-600 dark:text-neutral-400">
          Real-time task processing status across all agencies
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Total Tasks</p>
              <p className="text-title text-neutral-900 dark:text-neutral-100">
                {stats.total}
              </p>
            </div>
            <ClockIcon className="h-8 w-8 text-neutral-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Pending</p>
              <p className="text-title text-neutral-900 dark:text-neutral-100">
                {stats.pending}
              </p>
            </div>
            <ClockIcon className="h-8 w-8 text-neutral-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Processing</p>
              <p className="text-title text-brand-600">
                {stats.processing}
              </p>
            </div>
            <ArrowPathIcon className="h-8 w-8 text-brand-400 animate-spin" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Completed</p>
              <p className="text-title text-success-600">
                {stats.completed}
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-success-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Failed</p>
              <p className="text-title text-error-600">
                {stats.failed}
              </p>
            </div>
            <XCircleIcon className="h-8 w-8 text-error-400" />
          </div>
        </div>
      </div>

      {/* Task List */}
      <div className="fluent-card">
        <div className="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100">
            Recent Tasks
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
            <thead className="bg-neutral-50 dark:bg-neutral-800">
              <tr>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Kind
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Priority
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Attempts
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-neutral-900 divide-y divide-neutral-200 dark:divide-neutral-700">
              {tasks.map((task) => {
                const StatusIcon = statusConfig[task.status].icon
                return (
                  <tr key={task.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800">
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                      {task.kind}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`status-badge ${statusConfig[task.status].className}`}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {statusConfig[task.status].label}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                      {task.priority}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                      {task.attempts} / {task.max_attempts}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-500 dark:text-neutral-400">
                      {new Date(task.created_at).toLocaleString('en-PH', {
                        timeZone: 'Asia/Manila',
                        dateStyle: 'short',
                        timeStyle: 'short',
                      })}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
