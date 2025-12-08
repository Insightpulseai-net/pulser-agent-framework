'use client'

import { useEffect, useState } from 'react'
import { supabase, BIRFormRow, BIRStatus } from '@/lib/supabase'
import {
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationCircleIcon,
  ClockIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { format } from 'date-fns'

const statusConfig: Record<BIRStatus, { label: string; className: string; icon: any }> = {
  not_started: {
    label: 'Not Started',
    className: 'status-neutral',
    icon: ClockIcon,
  },
  in_progress: {
    label: 'In Progress',
    className: 'status-info',
    icon: DocumentTextIcon,
  },
  submitted: {
    label: 'Submitted',
    className: 'status-warning',
    icon: ExclamationCircleIcon,
  },
  filed: {
    label: 'Filed',
    className: 'status-success',
    icon: CheckCircleIcon,
  },
  late: {
    label: 'Filed Late',
    className: 'status-warning',
    icon: ExclamationCircleIcon,
  },
  overdue: {
    label: 'Overdue',
    className: 'status-error',
    icon: XCircleIcon,
  },
  rejected: {
    label: 'Rejected',
    className: 'status-error',
    icon: XCircleIcon,
  },
}

const formTypes = [
  { code: '1601-C', name: 'Monthly Remittance (Compensation)' },
  { code: '0619-E', name: 'Monthly Remittance (Expanded)' },
  { code: '2550Q', name: 'Quarterly Income Tax' },
  { code: '1702-RT', name: 'Annual Reconciliation' },
  { code: '1601-EQ', name: 'Quarterly Remittance (Expanded)' },
  { code: '1601-FQ', name: 'Quarterly Remittance (Final)' },
  { code: '2550M', name: 'Monthly Income Tax' },
  { code: '1600', name: 'Monthly Withholding Tax' },
]

export default function BIRStatusDashboard() {
  const [forms, setForms] = useState<BIRFormRow[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    total: 0,
    filed: 0,
    overdue: 0,
    pending: 0,
    complianceRate: 0,
  })

  useEffect(() => {
    fetchForms()
    fetchStats()

    // Subscribe to real-time updates
    const channel = supabase
      .channel('bir_forms_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'scout', table: 'silver_bir_forms' },
        () => {
          fetchForms()
          fetchStats()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  async function fetchForms() {
    const { data, error } = await supabase
      .from('silver_bir_forms')
      .select('*')
      .order('filing_deadline', { ascending: true })
      .limit(50)

    if (data) {
      setForms(data as BIRFormRow[])
    }
    setLoading(false)
  }

  async function fetchStats() {
    const { data, error } = await supabase
      .from('silver_bir_forms')
      .select('status, filed_date, filing_deadline')

    if (data) {
      const total = data.length
      const filed = data.filter((f) => f.status === 'filed').length
      const overdue = data.filter((f) => f.status === 'overdue').length
      const pending = data.filter((f) =>
        ['not_started', 'in_progress', 'submitted'].includes(f.status)
      ).length
      const complianceRate = total > 0 ? Math.round((filed / total) * 100) : 0

      setStats({ total, filed, overdue, pending, complianceRate })
    }
  }

  function getDaysUntilDeadline(deadline: string): number {
    const now = new Date()
    const deadlineDate = new Date(deadline)
    const diff = deadlineDate.getTime() - now.getTime()
    return Math.ceil(diff / (1000 * 60 * 60 * 24))
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <DocumentTextIcon className="h-8 w-8 animate-pulse text-brand-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-title-large text-neutral-900 dark:text-neutral-100">
          BIR Status Dashboard
        </h1>
        <p className="mt-2 text-body text-neutral-600 dark:text-neutral-400">
          Multi-agency BIR filing compliance tracking with 3-level approval workflow
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Total Forms</p>
              <p className="text-title text-neutral-900 dark:text-neutral-100">
                {stats.total}
              </p>
            </div>
            <DocumentTextIcon className="h-8 w-8 text-neutral-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Filed</p>
              <p className="text-title text-success-600">{stats.filed}</p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-success-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Overdue</p>
              <p className="text-title text-error-600">{stats.overdue}</p>
            </div>
            <XCircleIcon className="h-8 w-8 text-error-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Pending</p>
              <p className="text-title text-warning-600">{stats.pending}</p>
            </div>
            <ClockIcon className="h-8 w-8 text-warning-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Compliance</p>
              <p className="text-title text-brand-600">
                {stats.complianceRate}%
              </p>
            </div>
            <div className="text-body-large text-brand-400 font-semibold">
              {stats.complianceRate >= 95 ? '✓' : '!'}
            </div>
          </div>
        </div>
      </div>

      {/* Form Types Reference */}
      <div className="fluent-card p-6">
        <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-4">
          BIR Form Types
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {formTypes.map((ft) => (
            <div
              key={ft.code}
              className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 rounded-fluent"
            >
              <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
                {ft.code}
              </p>
              <p className="text-caption text-neutral-600 dark:text-neutral-400">
                {ft.name}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Forms List */}
      <div className="fluent-card">
        <div className="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100">
            Upcoming & Recent Filings
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
            <thead className="bg-neutral-50 dark:bg-neutral-800">
              <tr>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Form Type
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Period
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Agency
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Employee
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Deadline
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-neutral-900 divide-y divide-neutral-200 dark:divide-neutral-700">
              {forms.map((form) => {
                const StatusIcon = statusConfig[form.status].icon
                const daysUntil = getDaysUntilDeadline(form.filing_deadline)
                const isUrgent = daysUntil <= 3 && form.status !== 'filed'

                return (
                  <tr
                    key={form.id}
                    className={`hover:bg-neutral-50 dark:hover:bg-neutral-800 ${
                      isUrgent ? 'bg-error-50 dark:bg-error-900/10' : ''
                    }`}
                  >
                    <td className="px-6 py-4 whitespace-nowrap text-body font-medium text-neutral-900 dark:text-neutral-100">
                      {form.form_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                      {form.filing_period}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-600 dark:text-neutral-400">
                      {form.agency_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-600 dark:text-neutral-400">
                      {form.employee_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                      {format(new Date(form.filing_deadline), 'MMM dd, yyyy')}
                      {isUrgent && (
                        <span className="ml-2 text-error-600 font-medium">
                          ({daysUntil} days)
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`status-badge ${statusConfig[form.status].className}`}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {statusConfig[form.status].label}
                      </span>
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
