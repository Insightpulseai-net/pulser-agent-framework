import Link from 'next/link'
import {
  QueueListIcon,
  DocumentTextIcon,
  ChartBarIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline'

const features = [
  {
    name: 'Task Queue Monitor',
    description: 'Real-time task processing status across all agencies with automatic escalation and retry logic.',
    href: '/dashboard/task-queue',
    icon: QueueListIcon,
    stats: { label: 'Active Tasks', value: '24' },
    color: 'brand',
  },
  {
    name: 'BIR Status Dashboard',
    description: 'Multi-agency BIR filing compliance tracking with 3-level approval workflow and deadline alerts.',
    href: '/dashboard/bir-status',
    icon: DocumentTextIcon,
    stats: { label: 'Forms Due', value: '8' },
    color: 'success',
  },
  {
    name: 'OCR Confidence Metrics',
    description: 'PaddleOCR-VL accuracy monitoring with confidence thresholds and data quality validation.',
    href: '/dashboard/ocr-confidence',
    icon: ChartBarIcon,
    stats: { label: 'Avg Confidence', value: '94%' },
    color: 'warning',
  },
]

const agencies = [
  'TBWA\\Santiago Mangada Puno',
  'TBWA\\SMP',
  'TBWA\\Strategic Data Corp',
  'TBWA\\Chiat\\Day Philippines',
  'TBWA\\Free',
  'TBWA\\Digital Arts Network',
  'Digitas Philippines',
  'C&M Consulting',
]

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center px-4 py-2 rounded-full bg-brand-100 dark:bg-brand-900 text-brand-800 dark:text-brand-100 text-sm font-medium">
          <SparklesIcon className="h-4 w-4 mr-2" />
          AI-Powered Finance Operations
        </div>
        <h1 className="text-display text-neutral-900 dark:text-neutral-100">
          Finance Shared Services Center
        </h1>
        <p className="text-body-large text-neutral-600 dark:text-neutral-400 max-w-3xl mx-auto">
          Medallion architecture (Bronze → Silver → Gold → Platinum) powering 8 agencies with
          automated BIR compliance, intelligent expense processing, and real-time analytics.
        </p>
      </div>

      {/* Dashboard Cards */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((feature) => (
          <Link
            key={feature.name}
            href={feature.href}
            className="fluent-card-interactive p-6 space-y-4"
          >
            <div className="flex items-center justify-between">
              <div className={`p-3 rounded-fluent-lg bg-${feature.color}-100 dark:bg-${feature.color}-900`}>
                <feature.icon className={`h-6 w-6 text-${feature.color}-600 dark:text-${feature.color}-100`} />
              </div>
              <div className="text-right">
                <p className="text-caption text-neutral-500 dark:text-neutral-400">
                  {feature.stats.label}
                </p>
                <p className="text-title text-neutral-900 dark:text-neutral-100">
                  {feature.stats.value}
                </p>
              </div>
            </div>
            <div>
              <h3 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-2">
                {feature.name}
              </h3>
              <p className="text-body text-neutral-600 dark:text-neutral-400">
                {feature.description}
              </p>
            </div>
          </Link>
        ))}
      </div>

      {/* Agency Coverage */}
      <div className="fluent-card p-6">
        <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-4">
          Multi-Agency Coverage ({agencies.length} Agencies)
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {agencies.map((agency) => (
            <div
              key={agency}
              className="px-4 py-3 bg-neutral-100 dark:bg-neutral-700 rounded-fluent text-body text-neutral-900 dark:text-neutral-100"
            >
              {agency}
            </div>
          ))}
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        <div className="fluent-card p-6 space-y-2">
          <p className="text-caption text-neutral-500 dark:text-neutral-400">
            Total Employees
          </p>
          <p className="text-title-large text-neutral-900 dark:text-neutral-100">
            8
          </p>
          <p className="text-caption text-success-600">
            ↑ Full SSC Coverage
          </p>
        </div>
        <div className="fluent-card p-6 space-y-2">
          <p className="text-caption text-neutral-500 dark:text-neutral-400">
            BIR Forms Tracked
          </p>
          <p className="text-title-large text-neutral-900 dark:text-neutral-100">
            8
          </p>
          <p className="text-caption text-brand-600">
            1601-C, 2550Q, 0619-E, 1702-RT +4
          </p>
        </div>
        <div className="fluent-card p-6 space-y-2">
          <p className="text-caption text-neutral-500 dark:text-neutral-400">
            Compliance Rate
          </p>
          <p className="text-title-large text-neutral-900 dark:text-neutral-100">
            98.5%
          </p>
          <p className="text-caption text-success-600">
            ↑ On-time Filing
          </p>
        </div>
        <div className="fluent-card p-6 space-y-2">
          <p className="text-caption text-neutral-500 dark:text-neutral-400">
            OCR Accuracy
          </p>
          <p className="text-title-large text-neutral-900 dark:text-neutral-100">
            94.2%
          </p>
          <p className="text-caption text-warning-600">
            ↑ PaddleOCR-VL-900M
          </p>
        </div>
      </div>

      {/* System Architecture */}
      <div className="fluent-card p-6">
        <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-4">
          Medallion Architecture Pipeline
        </h2>
        <div className="flex items-center justify-between space-x-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-neutral-400"></div>
              <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
                Bronze
              </p>
            </div>
            <p className="text-body text-neutral-600 dark:text-neutral-400">
              Raw ingestion (BIGSERIAL, jsonb)
            </p>
          </div>
          <div className="text-neutral-400">→</div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-neutral-500"></div>
              <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
                Silver
              </p>
            </div>
            <p className="text-body text-neutral-600 dark:text-neutral-400">
              Validated entities (uuid, RLS)
            </p>
          </div>
          <div className="text-neutral-400">→</div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-warning-500"></div>
              <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
                Gold
              </p>
            </div>
            <p className="text-body text-neutral-600 dark:text-neutral-400">
              Analytics marts (MVs)
            </p>
          </div>
          <div className="text-neutral-400">→</div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center space-x-2">
              <div className="w-3 h-3 rounded-full bg-brand-500"></div>
              <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
                Platinum
              </p>
            </div>
            <p className="text-body text-neutral-600 dark:text-neutral-400">
              Vector embeddings (RAG)
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
