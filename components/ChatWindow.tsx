'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

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
// Sample questions
// ---------------------------------------------------------------------------

const SAMPLE_QUESTIONS = [
  { label: 'What is NAV?', sub: 'Learn the basics', icon: 'trending_up' },
  { label: 'How do exit loads work?', sub: 'Redemption rules', icon: 'account_balance' },
  { label: 'Is ELSS the same as tax saver fund?', sub: 'Tax efficiency', icon: 'savings' },
  { label: 'What is a lock-in period?', sub: 'Investment duration', icon: 'lock' },
  { label: 'Direct vs Regular plan difference?', sub: 'Expense ratio', icon: 'compare_arrows' },
]

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function UserBubble({ text }: { text: string }) {
  return (
    <div className="flex flex-col items-end w-full">
      <div className="bg-blue-700 text-white px-5 py-3 rounded-xl rounded-br-sm font-medium shadow-md shadow-blue-900/10 max-w-[80%]">
        {text}
      </div>
    </div>
  )
}

function AssistantAvatar() {
  return (
    <div className="flex items-center gap-2 mb-2 ml-1">
      <div className="w-6 h-6 bg-blue-900 rounded-full flex items-center justify-center shrink-0">
        <span className="material-symbols-outlined text-white" style={{ fontSize: 14, fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
      </div>
      <span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Mutual Fund FAQ</span>
    </div>
  )
}

function AnswerCard({ msg }: { msg: AnswerMessage }) {
  return (
    <div className="flex flex-col items-start max-w-[88%]">
      <AssistantAvatar />
      <div className="bg-white border border-gray-100 p-5 rounded-xl rounded-bl-sm text-gray-800 leading-relaxed shadow-sm text-sm whitespace-pre-line">
        {msg.text}
      </div>
      {msg.sourceUrl && (
        <div className="mt-2 ml-1 flex flex-col gap-0.5">
          <a href={msg.sourceUrl} target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-1.5 text-blue-600 font-medium text-xs hover:underline">
            <span className="material-symbols-outlined" style={{ fontSize: 13 }}>link</span>
            Official Source
          </a>
          {msg.lastUpdated && (
            <span className="text-[10px] uppercase tracking-tighter text-slate-400 font-bold ml-5">
              Last updated: {msg.lastUpdated.slice(0, 10)}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

function RefusalCard({ msg }: { msg: RefusalMessage }) {
  const isPii     = msg.reason?.startsWith('pii_')
  const isOOScope = msg.reason === 'out_of_scope'
  return (
    <div className="flex flex-col items-start max-w-[88%]">
      <AssistantAvatar />
      <div className={`p-5 rounded-xl rounded-bl-sm text-sm shadow-sm border ${
        isPii
          ? 'border-red-200 bg-red-50 text-red-700'
          : isOOScope
          ? 'border-gray-200 bg-gray-50 text-gray-600'
          : 'border-amber-200 bg-amber-50 text-amber-700'
      }`}>
        {msg.message}
      </div>
    </div>
  )
}

function TypingIndicator() {
  return (
    <div className="flex flex-col items-start max-w-[88%]">
      <AssistantAvatar />
      <div className="bg-white border border-gray-100 px-5 py-4 rounded-xl rounded-bl-sm shadow-sm">
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
// Main
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
    <div className="flex flex-col h-screen bg-[#f8f9fa]">
      {/* Fixed header */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-8 h-16 bg-white/80 backdrop-blur-xl border-b border-gray-100 shadow-sm">
        <h1 className="text-xl font-bold tracking-tight text-blue-900">Mutual Fund FAQ</h1>
        <Link href="/sources"
          className="bg-blue-700 text-white px-5 py-2 rounded-full font-semibold text-sm hover:bg-blue-800 transition-colors">
          View Sources
        </Link>
      </header>

      {/* Amber disclaimer */}
      <div className="fixed top-16 w-full z-40 bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center justify-center gap-2 text-amber-800">
        <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 18 }}>warning</span>
        <p className="text-xs font-medium">
          This tool provides general information only. Not financial advice. Consult a SEBI-registered advisor before investing.
        </p>
      </div>

      {/* Scrollable chat area */}
      <main className="flex-1 overflow-y-auto pt-32 pb-36">
        <div className="max-w-3xl mx-auto w-full px-6 lg:px-12 space-y-8">

          {/* Sample question cards */}
          {showSamples && (
            <>
              <h2 className="text-2xl font-bold text-blue-900 tracking-tight mt-6">How can I help your investment journey?</h2>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                {SAMPLE_QUESTIONS.slice(0, 3).map(q => (
                  <button key={q.label} onClick={() => submit(q.label)}
                    className="bg-white border border-gray-100 p-5 rounded-xl text-left hover:bg-blue-50 hover:border-blue-200 transition-colors group shadow-sm">
                    <span className="material-symbols-outlined text-blue-700 mb-2 block" style={{ fontSize: 24 }}>{q.icon}</span>
                    <p className="font-semibold text-gray-900 text-sm">{q.label}</p>
                    <p className="text-[11px] text-slate-400 mt-1 uppercase tracking-tighter">{q.sub}</p>
                  </button>
                ))}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {SAMPLE_QUESTIONS.slice(3).map(q => (
                  <button key={q.label} onClick={() => submit(q.label)}
                    className="bg-white border border-gray-100 p-5 rounded-xl text-left hover:bg-blue-50 hover:border-blue-200 transition-colors group shadow-sm">
                    <span className="material-symbols-outlined text-blue-700 mb-2 block" style={{ fontSize: 24 }}>{q.icon}</span>
                    <p className="font-semibold text-gray-900 text-sm">{q.label}</p>
                    <p className="text-[11px] text-slate-400 mt-1 uppercase tracking-tighter">{q.sub}</p>
                  </button>
                ))}
              </div>
            </>
          )}

          {/* Messages */}
          {messages.map((msg, i) => {
            if (msg.role === 'user') return <UserBubble key={i} text={msg.text} />
            if (msg.type === 'answer') return <AnswerCard key={i} msg={msg} />
            return <RefusalCard key={i} msg={msg} />
          })}

          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Fixed bottom input */}
      <div className="fixed bottom-0 w-full z-40 bg-white/60 backdrop-blur-xl border-t border-gray-100">
        <div className="max-w-3xl mx-auto px-6 lg:px-12 py-4">
          <form onSubmit={e => { e.preventDefault(); submit(input) }}
            className="relative flex items-center">
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about mutual funds…"
              disabled={loading}
              className="w-full bg-white border border-gray-200 rounded-full py-3.5 px-6 pr-28 shadow-lg shadow-blue-900/5 outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm text-gray-800 placeholder:text-gray-400 disabled:opacity-50 transition-all"
            />
            <button type="submit" disabled={loading || !input.trim()}
              className="absolute right-2 bg-blue-700 text-white px-5 py-2 rounded-full font-bold text-sm hover:bg-blue-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5">
              Ask
              <span className="material-symbols-outlined" style={{ fontSize: 16, fontVariationSettings: "'FILL' 1" }}>send</span>
            </button>
          </form>
          <p className="mt-2 text-center text-[10px] uppercase tracking-widest text-slate-400">
            Official AMC · AMFI · SEBI sources only ·{' '}
            <Link href="/sources" className="hover:text-blue-500 transition-colors">View all sources</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
