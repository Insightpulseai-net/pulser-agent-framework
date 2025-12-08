interface KPICardProps {
  title: string
  value: number | string
  trend: string
  icon: string
  onClick?: () => void
}

export default function KPICard({ title, value, trend, icon, onClick }: KPICardProps) {
  const trendIsPositive = trend.startsWith('+')

  return (
    <div
      onClick={onClick}
      className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 cursor-pointer hover:shadow-lg transition-shadow"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600 dark:text-gray-400">{title}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">{value}</p>
          <p className={`mt-2 text-sm ${trendIsPositive ? 'text-green-600' : 'text-red-600'}`}>
            {trend}
          </p>
        </div>
        <div className="text-4xl">{icon}</div>
      </div>
    </div>
  )
}
