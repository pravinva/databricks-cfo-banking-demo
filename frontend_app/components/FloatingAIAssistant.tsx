'use client'

import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Loader2, Sparkles, X, Minimize2, Maximize2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { apiFetch } from '@/lib/api'
import AssistantMessageContent from '@/components/AssistantMessageContent'

interface Message {
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
}

export default function FloatingAIAssistant() {
  const [isOpen, setIsOpen] = useState(false)
  const [isMinimized, setIsMinimized] = useState(false)
  const [isExpanded, setIsExpanded] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string>('')
  const [roomDisplayName, setRoomDisplayName] = useState<string>('Treasury Genie')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(scrollToBottom, [messages])

  useEffect(() => {
    try {
      const key = 'treasury_genie_conversation_id'
      const existing = window.localStorage.getItem(key)
      if (existing) {
        setConversationId(existing)
        return
      }
    } catch {
      // Ignore local storage issues and start fresh.
    }
  }, [])

  useEffect(() => {
    const openHandler = () => {
      setIsOpen(true)
      setIsMinimized(false)
      setIsExpanded(false)
    }

    window.addEventListener('open-treasury-genie', openHandler)
    return () => {
      window.removeEventListener('open-treasury-genie', openHandler)
    }
  }, [])

  useEffect(() => {
    const fetchRoomInfo = async () => {
      try {
        const response = await apiFetch('/api/genie/space')
        const data = await response.json()
        if (response.ok && data?.success && typeof data.display_name === 'string' && data.display_name.trim()) {
          setRoomDisplayName(data.display_name.trim())
        }
      } catch {
        // Keep default fallback room display name.
      }
    }

    fetchRoomInfo()
  }, [])

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
      const response = await apiFetch('/api/genie/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: input,
          conversation_id: conversationId || undefined,
        })
      })

      const data = await response.json()
      if (!response.ok || !data?.success) {
        throw new Error(data?.error || `HTTP ${response.status}`)
      }

      if (data?.conversation_id) {
        setConversationId(data.conversation_id)
        try {
          window.localStorage.setItem('treasury_genie_conversation_id', data.conversation_id)
        } catch {
          // Ignore storage failures.
        }
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: data.response || 'No response text returned by Genie.',
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (error) {
      console.error('Error:', error)
      const errorMessage: Message = {
        role: 'assistant',
        content: `Genie request failed: ${String((error as any)?.message || error)}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const quickQueries = [
    {
      label: 'CCAR Scenario Summary',
      prompt:
        'Give me a summary of all stress test scenarios - what rate shock each assumes, how depositor behavior changes under stress, the NII impact, and whether we pass the regulatory capital test.',
    },
    {
      label: 'Stable vs Vulnerable',
      prompt:
        'How is our deposit base distributed across rate sensitivity levels - how much of our funding is stable vs vulnerable to a rate move?',
    },
    {
      label: 'Profitability Trend 12M',
      prompt:
        'How has our operating profitability trended over the last 12 months and are we managing expenses efficiently relative to revenue?',
    },
    {
      label: 'Yield Curve Shape',
      prompt:
        'What does the current yield curve look like across short, medium, and long tenors - and what is it telling us about the rate environment?',
    },
    {
      label: 'At-Risk Accounts Top10',
      prompt:
        'Which specific customer relationships are most at risk of leaving today - who are our top 10 most vulnerable accounts and how far below market are we paying them?',
    },
    {
      label: 'Product Concentration Mix',
      prompt:
        'How is our current deposit base distributed across product types - where is our funding concentrated?',
    },
    {
      label: 'Portfolio Beta Today',
      prompt:
        'What is our total deposit portfolio beta today - how rate-sensitive is our entire funding base?',
    },
    {
      label: 'Runoff Concentration 3Y',
      prompt:
        'How much of our deposit base do we expect to lose over the next three years by each segment, and where is the runoff most concentrated?',
    },
    {
      label: 'Baseline vs Adverse',
      prompt:
        'Show me baseline deposit runoff, NII, and PPNR over the next two quarters and how these metrics change under the adverse scenario.',
    },
    {
      label: 'All Scenario NII',
      prompt:
        'How does NII change across all four rate scenarios over the next two quarters - and which scenario produces the largest compression?',
    },
  ]

  return (
    <>
      {/* Floating Button */}
      <AnimatePresence>
        {!isOpen && (
          <motion.div
            initial={{ scale: 0, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0, opacity: 0 }}
            className="fixed bottom-6 right-6 z-50"
          >
            <Button
              onClick={() => setIsOpen(true)}
              className="h-14 px-4 rounded-full bg-gradient-to-br from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 shadow-xl hover:shadow-2xl transition-all duration-300 group flex items-center gap-2"
            >
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
              >
                <Sparkles className="h-6 w-6 text-white" />
              </motion.div>
              <span className="text-white text-sm font-semibold tracking-wide">
                Ask me
              </span>
            </Button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Chat Window */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 100, scale: 0.8 }}
            animate={{
              opacity: 1,
              y: 0,
              scale: isMinimized ? 0.95 : 1,
              height: isMinimized ? 60 : isExpanded ? 760 : 600
            }}
            exit={{ opacity: 0, y: 100, scale: 0.8 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            className={`fixed bottom-6 right-6 z-50 ${isExpanded ? 'w-[min(92vw,1100px)]' : 'w-96'}`}
          >
            <Card className="border-slate-200 shadow-2xl overflow-hidden">
              {/* Header */}
              <div className="border-b border-slate-200 bg-gradient-to-r from-blue-600 to-blue-700 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <motion.div
                      animate={{ rotate: [0, 360] }}
                      transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                    >
                      <Sparkles className="h-5 w-5 text-white" />
                    </motion.div>
                    <div>
                      <h3 className="text-sm font-semibold text-white">Treasury Genie</h3>
                      <p className="text-xs text-blue-100">Room: {roomDisplayName}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {!isMinimized && (
                      <Button
                        variant="ghost"
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="hover:bg-blue-500/20 text-white p-1 h-7 w-7"
                        title={isExpanded ? 'Restore default size' : 'Expand window'}
                      >
                        {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                      </Button>
                    )}
                    <Button
                      variant="ghost"
                      onClick={() => {
                        if (!isMinimized) {
                          setIsExpanded(false)
                        }
                        setIsMinimized(!isMinimized)
                      }}
                      className="hover:bg-blue-500/20 text-white p-1 h-7 w-7"
                    >
                      <Minimize2 className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="ghost"
                      onClick={() => setIsOpen(false)}
                      className="hover:bg-blue-500/20 text-white p-1 h-7 w-7"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </div>

              {/* Content - Hidden when minimized */}
              {!isMinimized && (
                <div className={`flex flex-col ${isExpanded ? 'h-[696px]' : 'h-[536px]'}`}>
                  {/* Quick Queries (always visible) */}
                  <div className="bg-slate-50 p-3 border-b border-slate-200 flex-shrink-0">
                    <p className="text-xs font-medium text-slate-700 mb-2">Quick queries:</p>
                    <div className="flex gap-1.5 flex-wrap">
                      {quickQueries.map((query) => (
                        <button
                          key={query.label}
                          onClick={() => setInput(query.prompt)}
                          title={query.prompt}
                          className="text-xs px-2 py-1 rounded bg-white border border-slate-300 hover:border-blue-500 hover:bg-blue-50 transition-colors text-slate-700 hover:text-blue-700"
                        >
                          {query.label}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-white">
                    {messages.length === 0 && (
                      <div className="flex items-center justify-center h-full text-slate-400">
                        <div className="text-center">
                          <Sparkles className="h-10 w-10 mx-auto mb-3 opacity-50" />
                          <p className="text-xs">Ask about deposit models, PPNR, and yield curve drivers</p>
                        </div>
                      </div>
                    )}

                    <AnimatePresence>
                      {messages.map((message, index) => (
                        <motion.div
                          key={index}
                          initial={{ opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          exit={{ opacity: 0 }}
                          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[85%] rounded-lg p-3 ${
                              message.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-100 border border-slate-200 text-slate-900'
                            }`}
                          >
                            <AssistantMessageContent
                              content={message.content}
                              isUser={message.role === 'user'}
                            />
                            <p className={`text-xs mt-1 ${message.role === 'user' ? 'text-blue-200' : 'text-slate-500'}`}>
                              {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
                        <div className="bg-slate-100 border border-slate-200 rounded-lg p-3">
                          <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                        </div>
                      </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                  </div>

                  {/* Input */}
                  <div className="border-t border-slate-200 bg-white p-3 flex-shrink-0">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && !loading && handleSend()}
                        placeholder="Ask me anything..."
                        className="flex-1 px-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-slate-900 placeholder:text-slate-400"
                        disabled={loading}
                      />
                      <Button
                        onClick={handleSend}
                        disabled={loading || !input.trim()}
                        className="bg-blue-600 hover:bg-blue-700 text-white px-4"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </Card>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}
