import type { Metadata } from 'next'
import './globals.css'
import Link from 'next/link'
import {
  HomeIcon,
  QueueListIcon,
  DocumentTextIcon,
  ChartBarIcon,
} from '@heroicons/react/24/outline'

export const metadata: Metadata = {
  title: 'Archi Agent Framework - Finance SSC Dashboard',
  description: 'Multi-agency Finance Shared Services Center powered by AI agents',
}

const navigation = [
  { name: 'Home', href: '/', icon: HomeIcon },
  { name: 'Task Queue', href: '/dashboard/task-queue', icon: QueueListIcon },
  { name: 'BIR Status', href: '/dashboard/bir-status', icon: DocumentTextIcon },
  { name: 'OCR Confidence', href: '/dashboard/ocr-confidence', icon: ChartBarIcon },
]

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="antialiased">
        <div className="min-h-screen bg-neutral-50 dark:bg-neutral-900">
          {/* Top Navigation Bar - Microsoft Fluent UI style */}
          <nav className="bg-white dark:bg-neutral-800 border-b border-neutral-200 dark:border-neutral-700">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between h-16">
                <div className="flex">
                  <div className="flex-shrink-0 flex items-center">
                    <h1 className="text-xl font-semibold text-brand-600">
                      Finance SSC
                    </h1>
                  </div>
                  <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                    {navigation.map((item) => (
                      <Link
                        key={item.name}
                        href={item.href}
                        className="inline-flex items-center px-1 pt-1 text-sm font-medium text-neutral-900 dark:text-neutral-100 hover:text-brand-600 border-b-2 border-transparent hover:border-brand-600 transition-colors"
                      >
                        <item.icon className="h-5 w-5 mr-2" />
                        {item.name}
                      </Link>
                    ))}
                  </div>
                </div>
                <div className="flex items-center">
                  <div className="text-sm text-neutral-500 dark:text-neutral-400">
                    Multi-Agency Finance Operations
                  </div>
                </div>
              </div>
            </div>
          </nav>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-white dark:bg-neutral-800 border-t border-neutral-200 dark:border-neutral-700 mt-12">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <p className="text-center text-sm text-neutral-500 dark:text-neutral-400">
                Powered by Archi Agent Framework • 8 Agencies • AI-First Operations
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
