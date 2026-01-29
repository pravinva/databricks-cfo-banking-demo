'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Sparkles, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import Link from 'next/link'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function AIAssistant() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  const handleSend = async () => {
    if (!input.trim() || loading) return

    const userMessage: Message = {
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: input,
          session_id: 'demo_session'
        })
      })

      const data = await response.json()

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const exampleQueries = [
    'Current 10Y Treasury yield',
    'Rate shock: +50 bps on MMDA',
    'LCR status',
    'Portfolio summary'
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6" style={{ color: '#000000' }}>
      <div className="max-w-4xl mx-auto">
        <Card className="border-slate-200 shadow-lg overflow-hidden">
          {/* Header */}
          <div className="border-b border-slate-200 bg-white p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <motion.div
                  animate={{ rotate: [0, 360] }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                >
                  <Sparkles className="h-6 w-6 text-primary-700" />
                </motion.div>
                <div>
                  <h1 className="text-2xl font-semibold text-slate-900">AI Assistant</h1>
                  <p className="text-sm text-slate-600 mt-1">
                    Powered by Claude Sonnet 4.5 with MLflow tracing
                  </p>
                </div>
              </div>
              <Link href="/">
                <Button
                  variant="ghost"
                  className="hover:bg-slate-100 text-slate-600 p-2"
                >
                  <X className="h-5 w-5" />
                </Button>
              </Link>
            </div>
          </div>

          {/* Example Queries */}
          <div className="bg-slate-50 p-4 border-b border-slate-200">
            <p className="text-xs font-medium text-black mb-2">Quick queries:</p>
            <div className="flex gap-2 flex-wrap">
              {exampleQueries.map(query => (
                <motion.button
                  key={query}
                  onClick={() => setInput(query)}
                  style={{ color: '#000000' }}
                  className="text-xs px-3 py-1.5 rounded-md bg-white border-2 border-slate-400 font-semibold hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700 transition-colors"
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                >
                  {query}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Messages */}
          <div className="h-[500px] overflow-y-auto p-6 space-y-4 bg-white">
            {messages.length === 0 && (
              <div className="flex items-center justify-center h-full text-slate-400">
                <div className="text-center">
                  <Sparkles className="h-12 w-12 mx-auto mb-4 opacity-50" />
                  <p className="text-sm">Ask me about Treasury, Risk, or Regulatory metrics</p>
                </div>
              </div>
            )}

            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg p-4 ${
                      message.role === 'user'
                        ? 'bg-gradient-to-br from-blue-600 to-blue-700 text-white shadow-md'
                        : 'bg-gradient-to-br from-slate-50 to-slate-100 border border-slate-300 text-slate-900 shadow-sm'
                    }`}
                  >
                    <div className="prose prose-sm max-w-none">
                      <pre className={`whitespace-pre-wrap font-sans ${message.role === 'assistant' ? 'text-slate-800' : 'text-white'}`}>{message.content}</pre>
                    </div>
                    <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-blue-200' : 'text-slate-600'}`}>
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>

            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="flex justify-start"
              >
                <div className="bg-slate-100 border border-slate-200 rounded-lg p-4">
                  <Loader2 className="h-5 w-5 animate-spin text-primary-700" />
                </div>
              </motion.div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-slate-200 bg-white p-4">
            <div className="flex gap-2">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                placeholder="Ask about Treasury, Risk, or Regulatory metrics..."
                className="flex-1 px-4 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                disabled={loading}
              />
              <Button
                onClick={handleSend}
                disabled={loading || !input.trim()}
                className="bg-primary-700 hover:bg-primary-800 text-white px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </Card>
      </div>
    </div>
  )
}
