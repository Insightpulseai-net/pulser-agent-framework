'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import PipelineCanvas from '@/components/PipelineCanvas'

interface Pipeline {
  id: string
  name: string
  description: string | null
  enabled: boolean
  domain: string | null
  created_at: string
}

export default function PipelinesPage() {
  const [pipelines, setPipelines] = useState<Pipeline[]>([])
  const [selectedPipeline, setSelectedPipeline] = useState<Pipeline | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchPipelines = async () => {
      const supabase = createClient()
      const { data } = await supabase
        .from('pipelines')
        .select('*')
        .order('created_at', { ascending: false })

      if (data) {
        setPipelines(data)
      }
      setLoading(false)
    }

    fetchPipelines()
  }, [])

  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Pipelines</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Create and manage data pipelines
        </p>
      </div>

      <div className="flex flex-col lg:flex-row gap-6 flex-1">
        {/* Pipeline List */}
        <div className="w-full lg:w-1/3 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Pipeline List
            </h2>
            <button className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
              + New
            </button>
          </div>

          {loading ? (
            <div className="text-center py-8 text-gray-500">Loading...</div>
          ) : (
            <div className="space-y-2">
              {pipelines.map((pipeline) => (
                <div
                  key={pipeline.id}
                  onClick={() => setSelectedPipeline(pipeline)}
                  className={`p-4 rounded-lg border cursor-pointer transition-colors ${
                    selectedPipeline?.id === pipeline.id
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                      : 'border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700/50'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">
                        {pipeline.name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                        {pipeline.description || 'No description'}
                      </p>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      pipeline.enabled
                        ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300'
                        : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {pipeline.enabled ? 'Active' : 'Inactive'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Pipeline Canvas */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow">
          {selectedPipeline ? (
            <PipelineCanvas pipelineId={selectedPipeline.id} />
          ) : (
            <div className="flex items-center justify-center h-full text-gray-500 dark:text-gray-400">
              Select a pipeline to view or create a new one
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
