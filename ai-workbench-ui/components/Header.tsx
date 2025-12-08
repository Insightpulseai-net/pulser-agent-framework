'use client'

import { useState } from 'react'

export default function Header() {
  const [user, setUser] = useState({ email: 'user@insightpulseai.net', role: 'engineer' })

  return (
    <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
      <div className="px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400">
            InsightPulse AI Workbench
          </h1>
        </div>

        <div className="flex items-center space-x-4">
          {/* Search Bar */}
          <div className="hidden md:block">
            <input
              type="search"
              placeholder="Search tables, pipelines..."
              className="w-64 px-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* User Avatar */}
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
              {user.email.charAt(0).toUpperCase()}
            </div>
            <div className="hidden md:block">
              <div className="text-sm font-medium text-gray-900 dark:text-white">
                {user.email}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 capitalize">
                {user.role}
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
