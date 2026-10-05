import React from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Play, RefreshCw } from 'lucide-react'
import Markdown from '../Common/Markdown'
import CodeBlock from '../Common/CodeBlock'
import { ProgressBar, pct } from '../Common/ui'

const SOURCE = { llm: 'Freshly written', cache: 'From the lesson library', offline: 'Offline lesson' }

const Block = ({ label, children }) => (
  <section className="border-t border-ink-700/70 pt-8">
    <p className="eyebrow mb-4">{label}</p>
    {children}
  </section>
)

const LessonViewer = ({ lesson, topic, onTryCode, onRegenerate, regenerating }) => {
  const navigate = useNavigate()
  const data = lesson.lesson
  const meta = lesson.agent_metadata || {}

  return (
    <article className="card p-8 md:p-10 animate-fade-up">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap gap-2 text-xs">
          <span className="chip capitalize">{(meta.teaching_style || 'adaptive').replace('_', ' ')}</span>
          <span className="chip capitalize">{meta.complexity || lesson.difficulty}</span>
          {data?.estimated_minutes && <span className="chip">{data.estimated_minutes} min</span>}
          {lesson.source && <span className="chip">{SOURCE[lesson.source] || lesson.source}</span>}
        </div>
        {onRegenerate && (
          <button onClick={onRegenerate} disabled={regenerating} className="btn-ghost text-xs" title="Write a new variant">
            <RefreshCw className={`h-3.5 w-3.5 ${regenerating ? 'animate-spin' : ''}`} /> New variant
          </button>
        )}
      </div>

      {!data ? (
        <div className="mt-8"><Markdown>{lesson.content}</Markdown></div>
      ) : (
        <div className="space-y-10">
          <header className="mt-8">
            <h2 className="display text-4xl leading-tight">{data.title}</h2>
            {data.summary && <p className="mt-4 text-lg leading-8 text-fg-muted">{data.summary}</p>}
          </header>

          {data.objectives?.length > 0 && (
            <Block label="By the end you will">
              <ol className="space-y-3">
                {data.objectives.map((o, i) => (
                  <li key={i} className="flex gap-4 text-fg-muted">
                    <span className="font-serif text-lg leading-6 text-gold-400">{i + 1}</span>{o}
                  </li>
                ))}
              </ol>
            </Block>
          )}

          {data.sections?.map((s, i) => (
            <section key={i} className="border-t border-ink-700/70 pt-8">
              <h3 className="display mb-4 text-2xl">{s.title}</h3>
              <Markdown>{s.body_markdown}</Markdown>
            </section>
          ))}

          {data.code_examples?.length > 0 && (
            <Block label="Worked examples">
              <div className="space-y-8">
                {data.code_examples.map((ex, i) => (
                  <div key={i}>
                    <div className="flex items-center justify-between gap-4">
                      <h4 className="text-sm font-medium text-fg">{ex.title}</h4>
                      {onTryCode && (ex.language || 'python') === 'python' && (
                        <button onClick={() => onTryCode(ex.code)} className="btn-ghost text-xs">
                          <Play className="h-3.5 w-3.5" /> Run in playground
                        </button>
                      )}
                    </div>
                    <CodeBlock language={ex.language || 'python'}>{ex.code}</CodeBlock>
                    <Markdown className="text-sm">{ex.explanation}</Markdown>
                  </div>
                ))}
              </div>
            </Block>
          )}

          {data.key_takeaways?.length > 0 && (
            <Block label="Key takeaways">
              <ul className="space-y-3">
                {data.key_takeaways.map((t, i) => (
                  <li key={i} className="flex gap-3 text-fg-muted">
                    <span className="mt-2.5 h-1 w-1 flex-shrink-0 rounded-full bg-gold-400" />{t}
                  </li>
                ))}
              </ul>
            </Block>
          )}

          {data.practice && (
            <div className="rounded-2xl border border-gold-500/25 bg-gold-400/[0.04] p-6">
              <p className="eyebrow mb-3 text-gold-400/80">Practice challenge</p>
              <Markdown>{data.practice.prompt}</Markdown>
              <p className="mt-3 text-sm text-fg-subtle">
                Expected output <code className="inline-code">{data.practice.expected_output}</code>
              </p>
              {onTryCode && (
                <button onClick={() => onTryCode(data.practice.starter_code, data.practice)} className="btn-primary mt-5">
                  Start the challenge <ArrowRight className="h-4 w-4" />
                </button>
              )}
            </div>
          )}
        </div>
      )}

      <footer className="mt-10 flex flex-col gap-6 border-t border-ink-700/70 pt-8 sm:flex-row sm:items-center sm:justify-between">
        <div className="w-full max-w-xs">
          <div className="mb-2 flex justify-between text-xs text-fg-subtle">
            <span>Your mastery of {topic.name}</span><span>{pct(lesson.knowledge_level)}</span>
          </div>
          <ProgressBar value={lesson.knowledge_level} />
        </div>
        <button onClick={() => navigate(`/quiz/${topic.id}`)} className="btn-secondary">
          Check your understanding <ArrowRight className="h-4 w-4" />
        </button>
      </footer>
    </article>
  )
}

export default LessonViewer
