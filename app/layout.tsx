import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Mutual Fund FAQ — Groww',
  description: 'Facts-only mutual fund information assistant. Official sources only.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-50 flex flex-col">
        {/* Disclaimer — always visible */}
        <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-800 text-center">
          This tool provides <strong>factual information only</strong> and is{' '}
          <strong>not investment advice</strong>. Consult a SEBI-registered financial
          advisor before investing. Data sourced from official AMC, AMFI, and SEBI documents.
        </div>

        {children}

        {/* Footer */}
        <footer className="mt-auto border-t border-gray-200 py-3 text-center text-xs text-gray-400">
          Data from official AMC · AMFI · SEBI sources only ·{' '}
          <a href="/sources" className="underline hover:text-gray-600">
            View all sources
          </a>
        </footer>
      </body>
    </html>
  )
}
