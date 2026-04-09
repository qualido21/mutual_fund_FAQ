import { readFileSync } from 'fs'
import { join } from 'path'
import Link from 'next/link'

interface Source {
  id: string
  url: string
  type: string
  scheme?: string
  description?: string
  fetched_at?: string
}

function loadSources(): Source[] {
  const raw = readFileSync(join(process.cwd(), 'data', 'sources.json'), 'utf-8')
  return JSON.parse(raw)
}

const TYPE_COLORS: Record<string, string> = {
  amfi: 'bg-blue-100 text-blue-700',
  amc:  'bg-green-100 text-green-700',
  sebi: 'bg-purple-100 text-purple-700',
}

export default function SourcesPage() {
  const sources = loadSources()

  return (
    <main className="max-w-5xl mx-auto px-4 py-8">
      <div className="mb-6 flex items-center gap-4">
        <Link href="/" className="text-sm text-blue-600 hover:underline">← Back to FAQ</Link>
        <h1 className="text-2xl font-bold text-gray-900">Corpus Sources</h1>
        <span className="rounded-full bg-gray-100 px-3 py-0.5 text-sm text-gray-600">
          {sources.length} documents
        </span>
      </div>

      <p className="mb-6 text-sm text-gray-500">
        All answers are grounded exclusively in the official documents listed below.
        No third-party blogs, news articles, or aggregators are used.
      </p>

      <div className="overflow-x-auto rounded-xl border border-gray-200 bg-white shadow-sm">
        <table className="w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-left">
            <tr>
              <th className="px-4 py-3 font-medium text-gray-600">#</th>
              <th className="px-4 py-3 font-medium text-gray-600">Type</th>
              <th className="px-4 py-3 font-medium text-gray-600">Scheme</th>
              <th className="px-4 py-3 font-medium text-gray-600">Description</th>
              <th className="px-4 py-3 font-medium text-gray-600">URL</th>
              <th className="px-4 py-3 font-medium text-gray-600">Fetched</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sources.map((s, i) => (
              <tr key={s.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 text-gray-400">{i + 1}</td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-medium uppercase ${TYPE_COLORS[s.type] ?? 'bg-gray-100 text-gray-600'}`}>
                    {s.type}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700 max-w-[180px] truncate">
                  {s.scheme ?? '—'}
                </td>
                <td className="px-4 py-3 text-gray-600 max-w-[200px] truncate">
                  {s.description ?? '—'}
                </td>
                <td className="px-4 py-3">
                  <a href={s.url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 hover:underline truncate block max-w-[240px]"
                    title={s.url}>
                    {s.url.replace(/^https?:\/\//, '').slice(0, 50)}
                    {s.url.length > 60 ? '…' : ''}
                  </a>
                </td>
                <td className="px-4 py-3 text-gray-400 whitespace-nowrap">
                  {s.fetched_at ? s.fetched_at.slice(0, 10) : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </main>
  )
}
