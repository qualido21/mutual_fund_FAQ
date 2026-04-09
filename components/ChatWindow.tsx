'use client'

import { useState, useRef, useEffect } from 'react'

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface UserMessage {
  role: 'user'
  text: string
}

interface AnswerMessage {
  role: 'assistant'
  type: 'answer'
  text: string
  sourceUrl: string
  lastUpdated: string
  scheme: string
}

interface RefusalMessage {
  role: 'assistant'
  type: 'refusal' | 'no_context'
  reason?: string
  message: string
}

type Message = UserMessage | AnswerMessage | RefusalMessage

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

const SAMPLE_QUESTIONS = [
  'What is the exit load for Mirae Asset Large Cap Fund?',
  'What is the lock-in period for Mirae Asset ELSS Tax Saver Fund?',
  'What is the minimum SIP amount for Mirae Asset ELSS?',
  'What is the benchmark index for Mirae Asset Liquid Fund?',
  'What is the riskometer rating of Mirae Asset Flexi Cap Fund?',
]

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[75%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-2.5 text-sm text-white shadow-sm">
        {text}
      </div>
    </div>
  )
}

function AnswerCard({ msg }: { msg: AnswerMessage }) {
  return (
    <div className="flex justify-start">
      <div className="max-w-[85%] rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-4 py-3 shadow-sm">
        <p className="text-sm text-gray-800 whitespace-pre-line leading-relaxed">{msg.text}</p>
        {msg.sourceUrl && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-blue-600 border-t border-gray-100 pt-2">
            <svg className="h-3 w-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
            </svg>
            <a href={msg.sourceUrl} target="_blank" rel="noopener noreferrer" className="hover:underline truncate max-w-[280px]">
              Official Source
            </a>
            {msg.lastUpdated && (
              <span className="text-gray-400">· {msg.lastUpdated.slice(0, 10)}</span>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

function RefusalCard({ msg }: { msg: RefusalMessage }) {
  const isOOScope = msg.reason === 'out_of_scope'
  const isPii     = msg.reason?.startsWith('pii_')
  return (
    <div className="flex justify-start">
      <div className={`max-w-[85%] rounded-2xl rounded-tl-sm border px-4 py-3 text-sm shadow-sm ${
        isPii
          ? 'border-red-200 bg-red-50 text-red-700'
          : isOOScope
          ? 'border-gray-200 bg-gray-50 text-gray-600'
          : 'border-orange-200 bg-orange-50 text-orange-700'
      }`}>
        <p>{msg.message}</p>
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex justify-start">
      <div className="rounded-2xl rounded-tl-sm border border-gray-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map(i => (
            <span key={i} className="h-2 w-2 rounded-full bg-gray-400 animate-bounce"
              style={{ animationDelay: `${i * 0.15}s` }} />
          ))}
        </div>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main chat window
// ---------------------------------------------------------------------------

export default function ChatWindow() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput]       = useState('')
  const [loading, setLoading]   = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function submit(question: string) {
    if (!question.trim() || loading) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', text: question }])
    setLoading(true)

    try {
      const res = await fetch('/api/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await res.json()

      if (data.type === 'answer') {
        setMessages(prev => [...prev, {
          role: 'assistant', type: 'answer',
          text: data.answer, sourceUrl: data.source_url,
          lastUpdated: data.last_updated, scheme: data.scheme,
        }])
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant', type: data.type,
          reason: data.reason, message: data.message,
        }])
      }
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant', type: 'refusal', reason: 'error',
        message: 'Something went wrong. Please try again.',
      }])
    } finally {
      setLoading(false)
    }
  }

  const showSamples = messages.length === 0 && !loading

  return (
    <div className="flex flex-col flex-1 max-w-2xl w-full mx-auto px-4 py-6">
      {/* Header */}
      <div className="mb-6 text-center">
        <h1 className="text-2xl font-bold text-gray-900">Mutual Fund FAQ</h1>
        <p className="mt-1 text-sm text-gray-500">
          Ask factual questions about Mirae Asset funds · Official sources only
        </p>
      </div>

      {/* Message list */}
      <div className="flex-1 space-y-4 overflow-y-auto min-h-[300px]">
        {showSamples && (
          <div className="space-y-3">
            <p className="text-xs text-center text-gray-400 uppercase tracking-wide">Try asking</p>
            {SAMPLE_QUESTIONS.map(q => (
              <button key={q} onClick={() => submit(q)}
                className="w-full text-left rounded-xl border border-gray-200 bg-white px-4 py-3 text-sm text-gray-700 shadow-sm hover:border-blue-300 hover:bg-blue-50 transition-colors">
                {q}
              </button>
            ))}
          </div>
        )}

        {messages.map((msg, i) => {
          if (msg.role === 'user') return <UserBubble key={i} text={msg.text} />
          if (msg.type === 'answer') return <AnswerCard key={i} msg={msg} />
          return <RefusalCard key={i} msg={msg} />
        })}

        {loading && <TypingIndicator />}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="mt-4">
        <form onSubmit={e => { e.preventDefault(); submit(input) }}
          className="flex gap-2 rounded-xl border border-gray-300 bg-white p-2 shadow-sm focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100">
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about expense ratio, exit load, SIP, lock-in…"
            disabled={loading}
            className="flex-1 bg-transparent px-2 py-1 text-sm text-gray-800 outline-none placeholder:text-gray-400 disabled:opacity-50"
          />
          <button type="submit" disabled={loading || !input.trim()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors">
            Ask
          </button>
        </form>
        <p className="mt-2 text-center text-xs text-gray-400">
          Factual information only · Not investment advice
        </p>
      </div>
    </div>
  )
}
