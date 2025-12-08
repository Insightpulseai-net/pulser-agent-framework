'use client'

import { useEffect, useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import DQScorecard from '@/components/DQScorecard'

interface Table {
  id: string
  schema_name: string
  table_name: string
  dq_score: number | null
}

export default function QualityPage() {
  const [tables, setTables] = useState<Table[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTables = async () => {
      const supabase = createClient()
      const { data } = await supabase
        .from('tables')
        .select('id, schema_name, table_name, dq_score')
        .order('dq_score', { ascending: false })

      if (data) {
        setTables(data)
      }
      setLoading(false)
    }

    fetchTables()
  }, [])

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Data Quality</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Monitor data quality metrics across all tables
        </p>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600 dark:text-gray-400">Loading quality metrics...</div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {tables.map((table) => (
            <DQScorecard key={table.id} table={table} />
          ))}
        </div>
      )}
    </div>
  )
}
