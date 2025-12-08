'use client'

import { useEffect, useState } from 'react'
import { supabase, ExpenseOCRRow } from '@/lib/supabase'
import {
  ChartBarIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  XCircleIcon,
} from '@heroicons/react/24/outline'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

interface ConfidenceStats {
  avgConfidence: number
  totalScans: number
  highConfidence: number // >= 0.80
  mediumConfidence: number // 0.60-0.79
  lowConfidence: number // < 0.60
}

export default function OCRConfidenceDashboard() {
  const [scans, setScans] = useState<ExpenseOCRRow[]>([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<ConfidenceStats>({
    avgConfidence: 0,
    totalScans: 0,
    highConfidence: 0,
    mediumConfidence: 0,
    lowConfidence: 0,
  })
  const [distributionData, setDistributionData] = useState<Array<{ range: string; count: number }>>([])

  useEffect(() => {
    fetchScans()
    fetchStats()

    // Subscribe to real-time updates
    const channel = supabase
      .channel('expense_ocr_changes')
      .on(
        'postgres_changes',
        { event: '*', schema: 'scout', table: 'silver_expense_ocr' },
        () => {
          fetchScans()
          fetchStats()
        }
      )
      .subscribe()

    return () => {
      supabase.removeChannel(channel)
    }
  }, [])

  async function fetchScans() {
    const { data, error } = await supabase
      .from('silver_expense_ocr')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(100)

    if (data) {
      setScans(data as ExpenseOCRRow[])
      calculateDistribution(data)
    }
    setLoading(false)
  }

  async function fetchStats() {
    const { data, error } = await supabase
      .from('silver_expense_ocr')
      .select('confidence_score')

    if (data) {
      const total = data.length
      const avgConfidence =
        total > 0
          ? data.reduce((sum, s) => sum + s.confidence_score, 0) / total
          : 0
      const highConfidence = data.filter((s) => s.confidence_score >= 0.8).length
      const mediumConfidence = data.filter(
        (s) => s.confidence_score >= 0.6 && s.confidence_score < 0.8
      ).length
      const lowConfidence = data.filter((s) => s.confidence_score < 0.6).length

      setStats({
        avgConfidence: Math.round(avgConfidence * 100) / 100,
        totalScans: total,
        highConfidence,
        mediumConfidence,
        lowConfidence,
      })
    }
  }

  function calculateDistribution(data: ExpenseOCRRow[]) {
    const ranges = [
      { range: '0.0-0.2', min: 0.0, max: 0.2 },
      { range: '0.2-0.4', min: 0.2, max: 0.4 },
      { range: '0.4-0.6', min: 0.4, max: 0.6 },
      { range: '0.6-0.8', min: 0.6, max: 0.8 },
      { range: '0.8-1.0', min: 0.8, max: 1.0 },
    ]

    const distribution = ranges.map((r) => ({
      range: r.range,
      count: data.filter(
        (s) => s.confidence_score >= r.min && s.confidence_score < r.max
      ).length,
    }))

    setDistributionData(distribution)
  }

  function getConfidenceColor(score: number): string {
    if (score >= 0.8) return 'text-success-600'
    if (score >= 0.6) return 'text-warning-600'
    return 'text-error-600'
  }

  function getConfidenceIcon(score: number) {
    if (score >= 0.8) return <CheckCircleIcon className="h-4 w-4 text-success-600" />
    if (score >= 0.6)
      return <ExclamationTriangleIcon className="h-4 w-4 text-warning-600" />
    return <XCircleIcon className="h-4 w-4 text-error-600" />
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <ChartBarIcon className="h-8 w-8 animate-pulse text-brand-600" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-title-large text-neutral-900 dark:text-neutral-100">
          OCR Confidence Metrics
        </h1>
        <p className="mt-2 text-body text-neutral-600 dark:text-neutral-400">
          PaddleOCR-VL-900M accuracy monitoring with confidence thresholds
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Avg Confidence</p>
              <p className={`text-title ${getConfidenceColor(stats.avgConfidence)}`}>
                {(stats.avgConfidence * 100).toFixed(1)}%
              </p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-neutral-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Total Scans</p>
              <p className="text-title text-neutral-900 dark:text-neutral-100">
                {stats.totalScans}
              </p>
            </div>
            <ChartBarIcon className="h-8 w-8 text-neutral-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">High (≥80%)</p>
              <p className="text-title text-success-600">
                {stats.highConfidence}
              </p>
            </div>
            <CheckCircleIcon className="h-8 w-8 text-success-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Medium (60-79%)</p>
              <p className="text-title text-warning-600">
                {stats.mediumConfidence}
              </p>
            </div>
            <ExclamationTriangleIcon className="h-8 w-8 text-warning-400" />
          </div>
        </div>
        <div className="fluent-card p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-caption text-neutral-500">Low (&lt;60%)</p>
              <p className="text-title text-error-600">
                {stats.lowConfidence}
              </p>
            </div>
            <XCircleIcon className="h-8 w-8 text-error-400" />
          </div>
        </div>
      </div>

      {/* Confidence Distribution Chart */}
      <div className="fluent-card p-6">
        <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-4">
          Confidence Score Distribution
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={distributionData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="range" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="count" radius={[8, 8, 0, 0]}>
              {distributionData.map((entry, index) => {
                let fill = '#22c55e' // success-500
                if (entry.range === '0.6-0.8') fill = '#eab308' // warning-500
                if (entry.range.startsWith('0.0') || entry.range.startsWith('0.2') || entry.range.startsWith('0.4')) {
                  fill = '#ef4444' // error-500
                }
                return <Cell key={`cell-${index}`} fill={fill} />
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
        <div className="mt-4 flex justify-center space-x-6 text-body">
          <div className="flex items-center">
            <div className="w-4 h-4 bg-success-500 rounded mr-2"></div>
            <span className="text-neutral-600 dark:text-neutral-400">
              High Confidence (≥80%)
            </span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-warning-500 rounded mr-2"></div>
            <span className="text-neutral-600 dark:text-neutral-400">
              Medium (60-79%)
            </span>
          </div>
          <div className="flex items-center">
            <div className="w-4 h-4 bg-error-500 rounded mr-2"></div>
            <span className="text-neutral-600 dark:text-neutral-400">Low (&lt;60%)</span>
          </div>
        </div>
      </div>

      {/* Recent Scans */}
      <div className="fluent-card">
        <div className="px-6 py-4 border-b border-neutral-200 dark:border-neutral-700">
          <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100">
            Recent OCR Scans
          </h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-neutral-200 dark:divide-neutral-700">
            <thead className="bg-neutral-50 dark:bg-neutral-800">
              <tr>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Vendor
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Amount
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Date
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Confidence
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-caption font-medium text-neutral-500 uppercase tracking-wider">
                  Scanned At
                </th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-neutral-900 divide-y divide-neutral-200 dark:divide-neutral-700">
              {scans.slice(0, 20).map((scan) => (
                <tr key={scan.id} className="hover:bg-neutral-50 dark:hover:bg-neutral-800">
                  <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                    {scan.vendor_name || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-900 dark:text-neutral-100">
                    {scan.amount ? `₱${scan.amount.toLocaleString()}` : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-600 dark:text-neutral-400">
                    {scan.date || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      {getConfidenceIcon(scan.confidence_score)}
                      <span className={`text-body ${getConfidenceColor(scan.confidence_score)}`}>
                        {(scan.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`status-badge ${
                        scan.status === 'validated'
                          ? 'status-success'
                          : scan.status === 'needs_review'
                          ? 'status-warning'
                          : 'status-neutral'
                      }`}
                    >
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-body text-neutral-500 dark:text-neutral-400">
                    {new Date(scan.created_at).toLocaleString('en-PH', {
                      timeZone: 'Asia/Manila',
                      dateStyle: 'short',
                      timeStyle: 'short',
                    })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Model Info */}
      <div className="fluent-card p-6">
        <h2 className="text-subtitle text-neutral-900 dark:text-neutral-100 mb-4">
          OCR Model Information
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <p className="text-caption text-neutral-500">Model</p>
            <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
              PaddleOCR-VL-900M
            </p>
          </div>
          <div>
            <p className="text-caption text-neutral-500">Confidence Threshold</p>
            <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
              ≥ 0.60 (60%)
            </p>
          </div>
          <div>
            <p className="text-caption text-neutral-500">LLM Post-Processing</p>
            <p className="text-body-large font-medium text-neutral-900 dark:text-neutral-100">
              GPT-4o-mini
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
