import React, { useMemo, useState } from 'react'

type ParsedQuestion = {
  question: string
  options: Record<string, string>
  correct_label?: string
  correct_text?: string
}

type RewrittenQuestion = ParsedQuestion & {
  reason?: string
  display?: {
    question: string
    answer: string
    reason: string
  }
}

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export default function App() {
  const [file, setFile] = useState<File | null>(null)
  const [parsedQuestions, setParsedQuestions] = useState<ParsedQuestion[]>([])
  const [processed, setProcessed] = useState<RewrittenQuestion[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const hasResults = processed.length > 0

  const formattedText = useMemo(() => {
    return processed
      .map((q) => [
        q.display?.question || `Question: ${q.question}`,
        q.display?.answer || (q.correct_label ? `✅ Correct Answer: ${q.correct_label}. ${q.options[q.correct_label] || ''}` : ''),
        q.display?.reason || (q.reason ? `Reason: ${q.reason}` : ''),
        ''
      ].join('\n'))
      .join('\n')
  }, [processed])

  async function handleUpload() {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const form = new FormData()
      form.append('file', file)
      const res = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'POST',
        body: form,
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setParsedQuestions(data.questions || [])
    } catch (e: any) {
      setError(e?.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }

  async function handleProcess() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/process`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ questions: parsedQuestions }),
      })
      if (!res.ok) throw new Error(await res.text())
      const data = await res.json()
      setProcessed(data.questions || [])
    } catch (e: any) {
      setError(e?.message || 'Processing failed')
    } finally {
      setLoading(false)
    }
  }

  function handleCopy() {
    navigator.clipboard.writeText(formattedText)
  }

  function handleDownload() {
    const blob = new Blob([JSON.stringify(processed, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'output.json'
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Quiz PDF Processor</h1>

      <div className="bg-white rounded-lg shadow p-4 space-y-3">
        <input
          type="file"
          accept="application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm"
        />
        <div className="flex gap-2">
          <button
            onClick={handleUpload}
            disabled={!file || loading}
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          >
            Upload & Parse
          </button>
          <button
            onClick={handleProcess}
            disabled={!parsedQuestions.length || loading}
            className="px-4 py-2 bg-emerald-600 text-white rounded disabled:opacity-50"
          >
            Rewrite & Reason
          </button>
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
      </div>

      {!!parsedQuestions.length && (
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="font-medium mb-2">Parsed Questions: {parsedQuestions.length}</h2>
          <ul className="list-disc pl-5 space-y-1 text-sm text-gray-700">
            {parsedQuestions.map((q, idx) => (
              <li key={idx}>{q.question.slice(0, 120)}{q.question.length > 120 ? '…' : ''}</li>
            ))}
          </ul>
        </div>
      )}

      {hasResults && (
        <div className="bg-white rounded-lg shadow p-4 space-y-4">
          <div className="flex gap-2">
            <button onClick={handleCopy} className="px-3 py-2 bg-gray-800 text-white rounded">Copy Formatted</button>
            <button onClick={handleDownload} className="px-3 py-2 bg-gray-800 text-white rounded">Download JSON</button>
          </div>
          <div className="space-y-6">
            {processed.map((q, idx) => (
              <div key={idx} className="border rounded p-3">
                <p className="font-medium">{q.display?.question || `Question: ${q.question}`}</p>
                {q.correct_label && (
                  <p className="mt-1">{q.display?.answer || `✅ Correct Answer: ${q.correct_label}. ${q.options[q.correct_label] || ''}`}</p>
                )}
                {(q.display?.reason || q.reason) && (
                  <p className="mt-1 text-sm text-gray-700">{q.display?.reason || `Reason: ${q.reason}`}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}


