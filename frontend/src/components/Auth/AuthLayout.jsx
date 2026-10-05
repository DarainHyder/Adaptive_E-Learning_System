import React from 'react'
import { Wordmark } from '../Layout/Sidebar'

const POINTS = [
  ['Knows what you know', 'A transformer knowledge-tracing model estimates your mastery of every topic after each answer.'],
  ['Teaches the way you learn', 'Specialised AI agents pick a teaching strategy, write the lesson and pitch every quiz at the right difficulty.'],
  ['Remembers for you', 'Spaced repetition brings topics back just before you would forget them.'],
]

const AuthLayout = ({ title, subtitle, children, footer }) => (
  <div className="grid min-h-screen lg:grid-cols-[1.1fr_1fr]">
    <section className="relative hidden overflow-hidden border-r border-ink-800 bg-ink-900 p-14 lg:flex lg:flex-col lg:justify-between">
      <div className="pointer-events-none absolute -left-40 -top-40 h-[480px] w-[480px] rounded-full bg-gold-400/[0.06] blur-3xl" />
      <Wordmark />
      <div className="relative max-w-md">
        <h2 className="display text-6xl leading-[1.05]">
          Learning that <em className="text-gold-300">adapts</em> to you.
        </h2>
        <ul className="mt-12 space-y-7">
          {POINTS.map(([t, d], i) => (
            <li key={t} className="flex gap-4">
              <span className="mt-0.5 font-serif text-lg text-gold-400">0{i + 1}</span>
              <div>
                <p className="text-sm font-medium text-fg">{t}</p>
                <p className="mt-1 text-sm leading-6 text-fg-subtle">{d}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <p className="text-xs text-fg-subtle">Built with LangGraph, LangChain and PyTorch.</p>
    </section>

    <section className="flex items-center justify-center px-6 py-16">
      <div className="w-full max-w-sm animate-fade-up">
        <div className="mb-10 lg:hidden"><Wordmark /></div>
        <h1 className="display text-4xl">{title}</h1>
        <p className="mt-2 text-sm text-fg-muted">{subtitle}</p>
        <div className="mt-10">{children}</div>
        <div className="mt-8 text-sm text-fg-subtle">{footer}</div>
      </div>
    </section>
  </div>
)

export const Field = ({ label, hint, ...props }) => (
  <label className="block">
    <span className="mb-2 block text-xs font-medium text-fg-muted">{label}</span>
    {props.children || <input className="input-field" {...props} />}
    {hint && <span className="mt-2 block text-xs text-fg-subtle">{hint}</span>}
  </label>
)

export default AuthLayout
