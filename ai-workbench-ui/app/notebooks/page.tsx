'use client'

export default function NotebooksPage() {
  return (
    <div className="space-y-6 h-full flex flex-col">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Notebooks</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Interactive data analysis notebooks
        </p>
      </div>

      <div className="flex-1 bg-white dark:bg-gray-800 rounded-lg shadow">
        <iframe
          src="http://localhost:8888"
          className="w-full h-full rounded-lg"
          title="JupyterHub"
        />
      </div>
    </div>
  )
}
