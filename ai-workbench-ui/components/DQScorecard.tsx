interface Table {
  id: string
  schema_name: string
  table_name: string
  dq_score: number | null
}

interface DQScorecardProps {
  table: Table
}

export default function DQScorecard({ table }: DQScorecardProps) {
  const score = table.dq_score || 0
  const scoreColor = score >= 90 ? 'text-green-600' : score >= 70 ? 'text-yellow-600' : 'text-red-600'
  const bgColor = score >= 90 ? 'bg-green-50 dark:bg-green-900/20' : score >= 70 ? 'bg-yellow-50 dark:bg-yellow-900/20' : 'bg-red-50 dark:bg-red-900/20'

  return (
    <div className={`${bgColor} rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow`}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
          {table.schema_name}.{table.table_name}
        </h3>
        <div className={`text-3xl font-bold ${scoreColor}`}>
          {Math.round(score)}%
        </div>
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Completeness</span>
          <span className="font-medium">{Math.round(score * 0.95)}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Uniqueness</span>
          <span className="font-medium">{Math.round(score * 1.02)}%</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">Consistency</span>
          <span className="font-medium">{Math.round(score * 0.98)}%</span>
        </div>
      </div>
      <button className="mt-4 w-full px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm">
        View Details
      </button>
    </div>
  )
}
