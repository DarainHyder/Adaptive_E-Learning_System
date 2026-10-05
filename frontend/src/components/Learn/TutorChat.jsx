import React, { useEffect, useRef, useState } from 'react'
import { ArrowUp, Trash2 } from 'lucide-react'
import { tutorAPI } from '../../services/api'
import Markdown from '../Common/Markdown'

const SUGGESTIONS = [
  'Explain this with a simple analogy',
  'Walk me through an example',
  'What do beginners get wrong here?',
  'Ask me one quick question',
]

const TutorChat = ({ topic }) => {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const scrollRef = useRef(null)

  useEffect(() => {
    let active = true
    tutorAPI.history(topic.id).then((r) => active && setMessages(r.data.messages || [])).catch(() => {})
    return () => { active = false }
  }, [topic.id])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, sending])

  const send = async (text) => {
    const message = (text ?? input).trim()
    if (!message || sending) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: message }])
    setSending(true)
    try {
      const r = await tutorAPI.chat(message, topic.id)
      setMessages((m) => [...m, { role: 'assistant', content: r.data.reply }])
    } catch {
      setMessages((m) => [...m, { role: 'assistant', content: '_Sorry, I could not reply just now._' }])
    } finally {
      setSending(false)
    }
  }

  const clear = async () => {
    await tutorAPI.clear(topic.id)
    setMessages([])
  }

  return (
    <section className="card flex h-[560px] flex-col p-0 xl:h-full">
      <header className="flex items-center justify-between border-b border-ink-700/70 px-5 py-4">
        <div>
          <p className="font-serif text-xl text-fg">Tutor</p>
          <p className="text-xs text-fg-subtle">Remembers this conversation</p>
        </div>
        {messages.length > 0 && (
          <button onClick={clear} className="text-fg-subtle transition-colors hover:text-bad" title="Clear conversation" aria-label="Clear conversation">
            <Trash2 className="h-4 w-4" />
          </button>
        )}
      </header>

      <div ref={scrollRef} className="flex-1 space-y-5 overflow-y-auto px-5 py-5">
        {messages.length === 0 && !sending && (
          <div className="flex h-full flex-col justify-end gap-2">
            <p className="mb-2 text-sm text-fg-subtle">Ask anything about {topic.name}, or start with:</p>
            {SUGGESTIONS.map((s) => (
              <button key={s} onClick={() => send(s)}
                className="rounded-xl border border-ink-700 px-3.5 py-2.5 text-left text-sm text-fg-muted transition-colors hover:border-ink-600 hover:text-fg">
                {s}
              </button>
            ))}
          </div>
        )}
        {messages.map((m, i) => m.role === 'user' ? (
          <div key={i} className="flex justify-end">
            <p className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-ink-800 px-4 py-2.5 text-sm text-fg">{m.content}</p>
          </div>
        ) : (
          <div key={i} className="flex gap-3">
            <span className="mt-2 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gold-400" />
            <Markdown className="min-w-0 text-sm">{m.content}</Markdown>
          </div>
        ))}
        {sending && (
          <div className="flex items-center gap-1.5 pl-4">
            {[0, 1, 2].map((d) => <span key={d} className="h-1.5 w-1.5 animate-pulse rounded-full bg-fg-subtle" style={{ animationDelay: `${d * 0.2}s` }} />)}
          </div>
        )}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); send() }} className="border-t border-ink-700/70 p-3">
        <div className="flex items-center gap-2 rounded-xl border border-ink-700 bg-ink-950 pl-4 pr-1.5 focus-within:border-gold-500/50">
          <input value={input} onChange={(e) => setInput(e.target.value)} maxLength={4000}
            placeholder="Ask the tutor…" className="flex-1 bg-transparent py-2.5 text-sm text-fg outline-none placeholder:text-fg-subtle" />
          <button type="submit" disabled={sending || !input.trim()} aria-label="Send"
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-gold-400 text-ink-950 transition-colors hover:bg-gold-300 disabled:bg-ink-700 disabled:text-fg-subtle">
            <ArrowUp className="h-4 w-4" />
          </button>
        </div>
      </form>
    </section>
  )
}

export default TutorChat
