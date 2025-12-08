'use client'

import { useState } from 'react'
import ChatInterface from '@/components/ChatInterface'

export default function GeniePage() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Genie (NL2SQL)</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Ask questions in natural language and get SQL queries
        </p>
      </div>

      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow">
        <ChatInterface />
      </div>
    </div>
  )
}
