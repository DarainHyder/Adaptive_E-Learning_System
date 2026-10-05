import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import toast from 'react-hot-toast'
import { quizAPI, topicAPI } from '../../services/api'
import TopicPicker from '../Common/TopicPicker'
import { PageHeader, PageLoader, Spinner, pct } from '../Common/ui'
import Question from './Question'
import Results from './Results'

const Quiz = () => {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const [topic, setTopic] = useState(null)
  const [quiz, setQuiz] = useState(null)
  const [index, setIndex] = useState(0)
  const [answers, setAnswers] = useState({})
  const [results, setResults] = useState(null)
  const [generating, setGenerating] = useState(false)
  const questionStart = useRef(Date.now())

  useEffect(() => {
    setTopic(null); setQuiz(null); setAnswers({}); setResults(null); setIndex(0)
    if (topicId) topicAPI.getById(topicId).then((r) => setTopic(r.data)).catch(() => navigate('/quiz'))
  }, [topicId])

  useEffect(() => { questionStart.current = Date.now() }, [index, quiz])

  const start = async () => {
    setGenerating(true)
    try {
      const r = await quizAPI.generateQuiz(topic.id)
      setQuiz(r.data); setIndex(0); setAnswers({}); setResults(null)
    } catch {
      toast.error('Could not assemble a quiz')
    } finally {
      setGenerating(false)
    }
  }

  const answer = async (i, choice) => {
    if (answers[i]) return
    const q = quiz.questions[i]
    setAnswers((a) => ({ ...a, [i]: { user_answer: choice, question: q.question, pending: true } }))
    try {
      // Graded server-side: the client never sees the answer key before answering
      const r = await quizAPI.submitAnswer({
        topic_id: topic.id, question_id: q.id, user_answer: choice,
        time_taken: Math.round((Date.now() - questionStart.current) / 1000),
      })
      setAnswers((a) => ({ ...a, [i]: { ...a[i], pending: false, ...r.data } }))
    } catch {
      setAnswers((a) => { const n = { ...a }; delete n[i]; return n })
    }
  }

  const finish = () => {
    const done = Object.values(answers).filter((a) => !a.pending)
    if (done.length < quiz.questions.length) {
      toast(`Answer all questions first (${done.length}/${quiz.questions.length})`)
      return
    }
    const correct = done.filter((a) => a.is_correct).length
    const last = answers[quiz.questions.length - 1]
    setResults({ score: (correct / done.length) * 100, correct, total: done.length, answers,
      topicName: topic.name, topicId: topic.id, mastery: last?.new_knowledge_level })
  }

  if (!topicId) {
    return (
      <>
        <PageHeader eyebrow="Practice" title="Test what you know"
          subtitle="Each quiz is pitched so you succeed about 70% of the time, the sweet spot for learning." />
        <TopicPicker onSelect={(t) => navigate(`/quiz/${t.id}`)} actionLabel="No attempts yet" />
      </>
    )
  }
  if (!topic) return <PageLoader />
  if (results) return <Results results={results} onRetake={start} />

  if (!quiz) {
    return (
      <div>
        <Link to="/quiz" className="btn-ghost mb-8"><ArrowLeft className="h-4 w-4" /> All topics</Link>
        <PageHeader eyebrow={`Practice · ${topic.category}`} title={topic.name} subtitle={topic.description} />
        <div className="card flex flex-col items-start gap-5 p-8 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="font-serif text-2xl text-fg">An adaptive quiz</p>
            <p className="mt-1 max-w-lg text-sm text-fg-subtle">
              The assessment agent predicts how you will do at each difficulty and mixes questions you have not seen yet.
            </p>
          </div>
          <button onClick={start} disabled={generating} className="btn-primary px-6 py-3">
            {generating ? <><Spinner /> Assembling…</> : <>Start quiz <ArrowRight className="h-4 w-4" /></>}
          </button>
        </div>
      </div>
    )
  }

  const total = quiz.questions.length
  const current = answers[index]
  const answeredCount = Object.values(answers).filter((a) => !a.pending).length
  const meta = quiz.agent_metadata || {}

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-10 flex items-center justify-between gap-4">
        <button onClick={() => setQuiz(null)} className="btn-ghost"><ArrowLeft className="h-4 w-4" /> {topic.name}</button>
        {meta.expected_success !== undefined && (
          <span className="text-xs text-fg-subtle">Predicted success {pct(meta.expected_success)}</span>
        )}
      </div>

      <div className="mb-8 flex items-center gap-4">
        <span className="font-mono text-xs text-fg-subtle">{String(index + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}</span>
        <div className="flex flex-1 gap-1.5">
          {quiz.questions.map((_, i) => {
            const a = answers[i]
            const color = a?.is_correct === true ? 'bg-ok' : a?.is_correct === false ? 'bg-bad' : i === index ? 'bg-gold-400' : 'bg-ink-700'
            return <button key={i} onClick={() => setIndex(i)} className={`h-1 flex-1 rounded-full transition-colors ${color}`} aria-label={`Question ${i + 1}`} />
          })}
        </div>
      </div>

      <Question key={quiz.questions[index].id ?? index} question={quiz.questions[index]}
        selectedAnswer={current?.user_answer} onAnswer={(c) => answer(index, c)}
        showResult={current?.is_correct !== undefined} pending={!!current?.pending} result={current} />

      <div className="mt-8 flex items-center justify-between">
        <button onClick={() => setIndex((i) => i - 1)} disabled={index === 0} className="btn-ghost disabled:invisible">
          <ArrowLeft className="h-4 w-4" /> Previous
        </button>
        {index === total - 1 ? (
          <button onClick={finish} disabled={answeredCount < total} className="btn-primary">See results</button>
        ) : (
          <button onClick={() => setIndex((i) => i + 1)} className={current?.is_correct !== undefined ? 'btn-primary' : 'btn-secondary'}>
            Next <ArrowRight className="h-4 w-4" />
          </button>
        )}
      </div>
    </div>
  )
}

export default Quiz
