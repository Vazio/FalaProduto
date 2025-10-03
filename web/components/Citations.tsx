'use client'

import type { Citation } from '@/app/page'

interface CitationsProps {
  citations: Citation[]
  onCitationClick: (citation: Citation) => void
}

export default function Citations({ citations, onCitationClick }: CitationsProps) {
  if (citations.length === 0) {
    return (
      <div className="p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          📄 Fontes Citadas
        </h2>
        <div className="text-center py-12">
          <div className="text-gray-400 dark:text-gray-600 mb-2">
            <svg
              className="w-16 h-16 mx-auto"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            As fontes aparecerão aqui quando fizer uma pergunta
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
        📄 Fontes Citadas
      </h2>
      <div className="space-y-4">
        {citations.map((citation, index) => (
          <div
            key={index}
            onClick={() => onCitationClick(citation)}
            className="bg-gray-50 dark:bg-gray-900 rounded-lg p-4 border border-gray-200 dark:border-gray-700 hover:border-primary-500 dark:hover:border-primary-500 transition-colors cursor-pointer"
          >
            {/* Header */}
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                  {citation.title}
                </h3>
                {citation.section && (
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">
                    {citation.section}
                  </p>
                )}
              </div>
              <span className="ml-2 flex-shrink-0 inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-800 dark:text-primary-200">
                p. {citation.page}
              </span>
            </div>

            {/* Excerpt */}
            <p className="text-xs text-gray-700 dark:text-gray-300 line-clamp-3 mb-2">
              {citation.excerpt}
            </p>

            {/* Score */}
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center">
                <svg className="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                Relevância: {(citation.score * 100).toFixed(0)}%
              </span>
              <span className="text-xs">
                #{index + 1}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          {citations.length} {citations.length === 1 ? 'fonte encontrada' : 'fontes encontradas'}
        </p>
      </div>
    </div>
  )
}


