'use client'

import { useState } from 'react'
import Chat from '@/components/Chat'
import Citations from '@/components/Citations'

export interface Citation {
  doc_id: string
  title: string
  section: string
  page: number
  score: number
  excerpt: string
}

export interface Message {
  role: 'user' | 'assistant'
  content: string
  citations?: Citation[]
  usage?: {
    total_latency_ms?: number
    tokens_prompt?: number
    tokens_completion?: number
    model?: string
  }
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [currentCitations, setCurrentCitations] = useState<Citation[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const handleSendMessage = async (query: string) => {
    // Add user message
    const userMessage: Message = { role: 'user', content: query }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const response = await fetch(`${apiUrl}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }

      const data = await response.json()

      // Add assistant message
      const assistantMessage: Message = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations,
        usage: data.usage,
      }

      setMessages(prev => [...prev, assistantMessage])
      setCurrentCitations(data.citations || [])
    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Desculpe, ocorreu um erro ao processar a sua pergunta. Por favor, tente novamente.',
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleCitationClick = (citation: Citation) => {
    console.log('Citation clicked:', citation)
    // Could implement modal or expand functionality here
  }

  return (
    <main className="flex min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              📚 Knowledge Base de Seguros
            </h1>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Pergunte sobre produtos de seguro e obtenha respostas com citações
            </p>
          </div>
        </header>

        {/* Chat Component */}
        <div className="flex-1 overflow-hidden">
          <Chat
            messages={messages}
            onSendMessage={handleSendMessage}
            isLoading={isLoading}
          />
        </div>
      </div>

      {/* Citations Sidebar */}
      <aside className="w-96 bg-white dark:bg-gray-800 border-l border-gray-200 dark:border-gray-700 overflow-y-auto">
        <Citations
          citations={currentCitations}
          onCitationClick={handleCitationClick}
        />
      </aside>
    </main>
  )
}


