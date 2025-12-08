'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navigation = [
  { name: 'Home', href: '/', icon: '🏠' },
  { name: 'Catalog', href: '/catalog', icon: '📚' },
  { name: 'SQL Editor', href: '/sql', icon: '📝' },
  { name: 'Pipelines', href: '/pipelines', icon: '🔄' },
  { name: 'Notebooks', href: '/notebooks', icon: '📓' },
  { name: 'Data Quality', href: '/quality', icon: '✅' },
  { name: 'Knowledge Graph', href: '/graph', icon: '🕸️' },
  { name: 'Genie (NL2SQL)', href: '/genie', icon: '🤖' },
]

export default function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
      <nav className="p-4 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={`flex items-center space-x-3 px-4 py-3 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-500 text-white'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <span className="text-xl">{item.icon}</span>
              <span className="font-medium">{item.name}</span>
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
