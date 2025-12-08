'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import TableBrowser from '@/components/TableBrowser'

interface Table {
  id: string
  schema_name: string
  table_name: string
  description: string | null
  row_count: number | null
  dq_score: number | null
}

export default function CatalogPage() {
  const [tables, setTables] = useState<Table[]>([])
  const [filteredTables, setFilteredTables] = useState<Table[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedSchema, setSelectedSchema] = useState<string>('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchTables = async () => {
      const supabase = createClient()
      const { data, error } = await supabase
        .from('tables')
        .select('*')
        .order('schema_name, table_name')

      if (data) {
        setTables(data)
        setFilteredTables(data)
      }
      setLoading(false)
    }

    fetchTables()
  }, [])

  useEffect(() => {
    let filtered = tables

    if (selectedSchema !== 'all') {
      filtered = filtered.filter(t => t.schema_name === selectedSchema)
    }

    if (searchQuery) {
      filtered = filtered.filter(t =>
        t.table_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.description?.toLowerCase().includes(searchQuery.toLowerCase())
      )
    }

    setFilteredTables(filtered)
  }, [searchQuery, selectedSchema, tables])

  const schemas = ['all', ...new Set(tables.map(t => t.schema_name))]

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Data Catalog</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Browse and search all tables in the Workbench
        </p>
      </div>

      {/* Search and Filter Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="search"
              placeholder="Search tables and columns..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              className="px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            >
              {schemas.map(schema => (
                <option key={schema} value={schema}>
                  {schema === 'all' ? 'All Schemas' : schema}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Table Browser */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-lg text-gray-600 dark:text-gray-400">Loading catalog...</div>
        </div>
      ) : (
        <TableBrowser tables={filteredTables} />
      )}
    </div>
  )
}
