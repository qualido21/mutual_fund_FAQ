import { readFileSync } from 'fs'
import { join } from 'path'
import Link from 'next/link'

interface Source {
  id:           string
  url:          string
  type:         string        // html | pdf
  source_type:  string        // amfi | amc | sebi
  scheme?:      string | null
  description?: string
  fetched_at?:  string
  fact_types?:  string[]
}

function loadSources(): Source[] {
  const raw = readFileSync(join(process.cwd(), 'data', 'sources.json'), 'utf-8')
  return JSON.parse(raw)
}

const SOURCE_COLORS: Record<string, string> = {
  amfi: 'bg-blue-100 text-blue-700',
  amc:  'bg-green-100 text-green-700',
  sebi: 'bg-purple-100 text-purple-700',
}

const DOC_COLORS: Record<string, string> = {
  html: 'bg-gray-100 text-gray-500',
  pdf:  'bg-red-50 text-red-500',
}

export default function SourcesPage() {
  const sources = loadSources()

  const bySourceType = {
    amfi: sources.filter(s => s.source_type === 'amfi'),
    amc:  sources.filter(s => s.source_type === 'amc'),
    sebi: sources.filter(s => s.source_type === 'sebi'),
  }

  return (
    <div className="flex flex-col min-h-screen bg-[#f8f9fa]">
      {/* Header */}
      <header className="fixed top-0 w-full z-50 flex justify-between items-center px-8 h-16 bg-white/80 backdrop-blur-xl border-b border-gray-100 shadow-sm">
        <h1 className="text-xl font-bold tracking-tight text-blue-900">Mutual Fund FAQ</h1>
        <Link href="/"
          className="bg-blue-700 text-white px-5 py-2 rounded-full font-semibold text-sm hover:bg-blue-800 transition-colors">
          ← Back to Chat
        </Link>
      </header>

      {/* Amber disclaimer */}
      <div className="fixed top-16 w-full z-40 bg-amber-50 border-b border-amber-200 px-6 py-2.5 flex items-center justify-center gap-2 text-amber-800">
        <span className="material-symbols-outlined text-amber-600" style={{ fontSize: 18 }}>warning</span>
        <p className="text-xs font-medium">
          This tool provides general information only. Not financial advice. Consult a SEBI-registered advisor before investing.
        </p>
      </div>

      <main className="flex-1 pt-32 pb-12 max-w-5xl mx-auto w-full px-6 lg:px-12">

        {/* Title row */}
        <div className="mb-2 flex items-center gap-4">
          <h2 className="text-2xl font-bold text-blue-900 tracking-tight">Corpus Sources</h2>
          <span className="rounded-full bg-gray-100 px-3 py-0.5 text-sm text-gray-500 font-medium">
            {sources.length} documents
          </span>
        </div>
        <p className="mb-8 text-sm text-gray-500">
          All answers are grounded exclusively in the official documents below.
          No third-party blogs, news, or aggregators are used.
        </p>

        {/* Summary badges */}
        <div className="mb-8 flex flex-wrap gap-3">
          {(['amfi', 'amc', 'sebi'] as const).map(t => (
            <div key={t} className={`flex items-center gap-2 px-4 py-2 rounded-full text-sm font-semibold ${SOURCE_COLORS[t]}`}>
              <span className="uppercase tracking-wide">{t}</span>
              <span className="opacity-70">{bySourceType[t].length} docs</span>
            </div>
          ))}
        </div>

        {/* Table */}
        <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
          <table className="w-full text-sm">
            <thead className="border-b border-gray-200 bg-gray-50 text-left">
              <tr>
                <th className="px-4 py-3 font-medium text-gray-600 w-8">#</th>
                <th className="px-4 py-3 font-medium text-gray-600">Source</th>
                <th className="px-4 py-3 font-medium text-gray-600">Doc</th>
                <th className="px-4 py-3 font-medium text-gray-600">Scheme</th>
                <th className="px-4 py-3 font-medium text-gray-600">Description</th>
                <th className="px-4 py-3 font-medium text-gray-600">URL</th>
                <th className="px-4 py-3 font-medium text-gray-600 whitespace-nowrap">Fetched</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {sources.map((s, i) => (
                <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-4 py-3 text-gray-400">{i + 1}</td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-bold uppercase tracking-wide ${SOURCE_COLORS[s.source_type] ?? 'bg-gray-100 text-gray-500'}`}>
                      {s.source_type}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`rounded-full px-2 py-0.5 text-xs font-medium uppercase ${DOC_COLORS[s.type] ?? 'bg-gray-100 text-gray-500'}`}>
                      {s.type}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-700 max-w-[160px]">
                    {s.scheme
                      ? <span className="font-medium">{s.scheme}</span>
                      : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-[240px] truncate" title={s.description}>
                    {s.description ?? '—'}
                  </td>
                  <td className="px-4 py-3 max-w-[220px]">
                    <a href={s.url} target="_blank" rel="noopener noreferrer"
                      className="text-blue-600 hover:underline truncate block"
                      title={s.url}>
                      {s.url.replace(/^https?:\/\//, '').slice(0, 45)}
                      {s.url.replace(/^https?:\/\//, '').length > 45 ? '…' : ''}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-gray-400 whitespace-nowrap text-xs">
                    {s.fetched_at ? s.fetched_at.slice(0, 10) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </main>
    </div>
  )
}
