'use client'

import { useState } from 'react'
import dynamic from 'next/dynamic'
import { createClient } from '@/lib/supabase/client'

const MonacoEditor = dynamic(() => import('@monaco-editor/react'), { ssr: false })

export default function SQLEditorPage() {
  const [sql, setSql] = useState('SELECT * FROM gold.finance_expenses LIMIT 10;')
  const [results, setResults] = useState<any[]>([])
  const [columns, setColumns] = useState<string[]>([])
  const [executing, setExecuting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [executionTime, setExecutionTime] = useState<number | null>(null)

  const executeQuery = async () => {
    setExecuting(true)
    setError(null)
    const startTime = Date.now()

    try {
      const supabase = createClient()
      const { data, error: queryError } = await supabase.rpc('execute_sql', { sql })

      if (queryError) {
        setError(queryError.message)
        setResults([])
        setColumns([])
      } else if (data && data.rows) {
        setResults(data.rows)
        setColumns(data.columns || [])
        setExecutionTime(Date.now() - startTime)
      }
    } catch (err: any) {
      setError(err.message)
      setResults([])
      setColumns([])
    } finally {
      setExecuting(false)
    }
  }

  return (
    <div className="space-y-4 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">SQL Editor</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Write and execute SQL queries against the Workbench database
        </p>
      </div>

      {/* Editor */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="h-64">
          <MonacoEditor
            height="100%"
            defaultLanguage="sql"
            value={sql}
            onChange={(value) => setSql(value || '')}
            theme="vs-dark"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              lineNumbers: 'on',
              automaticLayout: true,
            }}
          />
        </div>

        {/* Toolbar */}
        <div className="border-t border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
          <button
            onClick={executeQuery}
            disabled={executing}
            className="px-6 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-400 text-white rounded-lg font-medium transition-colors"
          >
            {executing ? 'Executing...' : 'Run Query'}
          </button>
          {executionTime && (
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Executed in {executionTime}ms • {results.length} rows
            </span>
          )}
        </div>
      </div>

      {/* Results */}
      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Query Results</h2>
        </div>
        <div className="overflow-auto max-h-96">
          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-800 dark:text-red-300">
              <strong>Error:</strong> {error}
            </div>
          )}
          {results.length > 0 && (
            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  {columns.map((col) => (
                    <th
                      key={col}
                      className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider"
                    >
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                {results.map((row, idx) => (
                  <tr key={idx}>
                    {columns.map((col) => (
                      <td key={col} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-white">
                        {JSON.stringify(row[col])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          {!error && results.length === 0 && (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              Run a query to see results
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
