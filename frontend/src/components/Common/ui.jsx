import React from 'react'

export const Spinner = ({ className = 'w-4 h-4' }) => (
  <span className={`inline-block animate-spin rounded-full border-2 border-current border-r-transparent ${className}`} />
)

export const PageLoader = ({ label }) => (
  <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-fg-subtle">
    <Spinner className="w-5 h-5 text-gold-400" />
    {label && <p className="text-sm">{label}</p>}
  </div>
)

export const PageHeader = ({ eyebrow, title, subtitle, actions, children }) => (
  <header className="mb-10 flex flex-col gap-6 md:flex-row md:items-end md:justify-between animate-fade-up">
    <div className="max-w-2xl">
      {eyebrow && <p className="eyebrow mb-3">{eyebrow}</p>}
      <h1 className="display text-4xl leading-tight md:text-5xl">{title}</h1>
      {subtitle && <p className="mt-3 text-fg-muted">{subtitle}</p>}
      {children}
    </div>
    {actions && <div className="flex flex-shrink-0 flex-wrap items-center gap-3">{actions}</div>}
  </header>
)

export const SectionTitle = ({ children, action }) => (
  <div className="mb-4 flex items-center justify-between">
    <h2 className="text-sm font-medium text-fg">{children}</h2>
    {action}
  </div>
)

export const Stat = ({ label, value, hint }) => (
  <div className="px-6 py-5">
    <p className="eyebrow">{label}</p>
    <p className="mt-2 font-serif text-4xl text-fg">{value}</p>
    {hint && <p className="mt-1 text-xs text-fg-subtle">{hint}</p>}
  </div>
)

export const StatStrip = ({ children }) => (
  <div className="grid grid-cols-2 divide-ink-700/70 overflow-hidden rounded-2xl border border-ink-700/70 bg-ink-900 lg:grid-cols-4 lg:divide-x [&>*:nth-child(-n+2)]:border-b [&>*:nth-child(-n+2)]:border-ink-700/70 lg:[&>*:nth-child(-n+2)]:border-b-0 [&>*:nth-child(odd)]:border-r [&>*:nth-child(odd)]:border-ink-700/70 lg:[&>*:nth-child(odd)]:border-r-0">
    {children}
  </div>
)

export const ProgressBar = ({ value = 0, tone = 'gold' }) => {
  const color = tone === 'ok' ? 'bg-ok' : tone === 'bad' ? 'bg-bad' : tone === 'muted' ? 'bg-ink-500' : 'bg-gold-400'
  return (
    <div className="track">
      <div className={`h-full rounded-full transition-[width] duration-700 ease-out ${color}`}
        style={{ width: `${Math.max(0, Math.min(1, value)) * 100}%` }} />
    </div>
  )
}

const LEVEL_DOTS = { beginner: 1, intermediate: 2, advanced: 3 }

export const DifficultyTag = ({ level }) => (
  <span className="chip capitalize" title={`${level} level`}>
    <span className="flex gap-0.5">
      {[1, 2, 3].map((i) => (
        <span key={i} className={`h-1 w-1 rounded-full ${i <= (LEVEL_DOTS[level] || 1) ? 'bg-gold-400' : 'bg-ink-600'}`} />
      ))}
    </span>
    {level}
  </span>
)

export const EmptyState = ({ title, children }) => (
  <div className="rounded-2xl border border-dashed border-ink-700 px-6 py-10 text-center">
    <p className="text-sm text-fg">{title}</p>
    {children && <p className="mt-1 text-sm text-fg-subtle">{children}</p>}
  </div>
)

export const pct = (v) => `${Math.round((v || 0) * 100)}%`
