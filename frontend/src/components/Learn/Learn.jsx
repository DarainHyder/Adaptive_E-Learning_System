import React, { useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Sparkles } from 'lucide-react'
import toast from 'react-hot-toast'
import { learningAPI, progressAPI, topicAPI } from '../../services/api'
import TopicPicker from '../Common/TopicPicker'
import { DifficultyTag, PageHeader, PageLoader, Spinner } from '../Common/ui'
import LessonViewer from './LessonViewer'
import CodePlayground from './CodePlayground'
import TutorChat from './TutorChat'

const Learn = () => {
  const { topicId } = useParams()
  const navigate = useNavigate()
  const [topic, setTopic] = useState(null)
  const [path, setPath] = useState(null)
  const [lesson, setLesson] = useState(null)
  const [generating, setGenerating] = useState(false)
  const [seed, setSeed] = useState(null)
  const playgroundRef = useRef(null)

  useEffect(() => {
    setTopic(null); setLesson(null); setPath(null); setSeed(null)
    if (!topicId) return
    topicAPI.getById(topicId).then((r) => setTopic(r.data)).catch(() => navigate('/learn'))
    progressAPI.getLearningPath(topicId).then((r) => setPath(r.data)).catch(() => {})
  }, [topicId])

  const generate = async (fresh = false) => {
    setGenerating(true)
    try {
      const r = await learningAPI.generateLesson(topic.id, fresh)
      setLesson(r.data)
      const practice = r.data.lesson?.practice
      setSeed(practice ? { code: practice.starter_code, practice } : null)
    } catch {
      toast.error('Could not prepare the lesson')
    } finally {
      setGenerating(false)
    }
  }

  const tryCode = (code, practice = null) => {
    setSeed({ code, practice })
    setTimeout(() => playgroundRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 50)
  }

  const nextTopic = async () => {
    try {
      const r = await progressAPI.getNextTopic(topic.id)
      navigate(`/learn/${r.data.id}`)
    } catch {
      toast('No further recommendation right now')
    }
  }

  if (!topicId) {
    return (
      <>
        <PageHeader eyebrow="Learn" title="What would you like to learn?"
          subtitle="Lessons are written for your current level by the teaching agent. Topics with unmet prerequisites are marked." />
        <TopicPicker onSelect={(t) => navigate(`/learn/${t.id}`)} actionLabel="Not started" />
      </>
    )
  }
  if (!topic) return <PageLoader />

  const before = path?.path?.filter((p) => p.topic_id !== topic.id) || []

  return (
    <div>
      <Link to="/learn" className="btn-ghost mb-8"><ArrowLeft className="h-4 w-4" /> All topics</Link>

      <PageHeader
        eyebrow={topic.category}
        title={topic.name}
        subtitle={topic.description}
        actions={lesson && <button onClick={nextTopic} className="btn-secondary">Next topic <ArrowRight className="h-4 w-4" /></button>}
      >
        <div className="mt-5 flex flex-wrap items-center gap-2">
          <DifficultyTag level={topic.difficulty} />
          {topic.key_concepts?.map((c) => <span key={c} className="chip">{c}</span>)}
        </div>
        {before.length > 0 && (
          <p className="mt-5 text-sm text-fg-subtle">
            Suggested first:{' '}
            {before.map((p, i) => (
              <React.Fragment key={p.topic_id}>
                {i > 0 && ' → '}
                <Link to={`/learn/${p.topic_id}`} className="link-gold">{p.name}</Link>
              </React.Fragment>
            ))}
          </p>
        )}
      </PageHeader>

      {!lesson ? (
        <div className="card flex flex-col items-start gap-5 p-8 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="font-serif text-2xl text-fg">Your personalised lesson</p>
            <p className="mt-1 max-w-lg text-sm text-fg-subtle">
              The knowledge agent reads your learner model, the teaching agent picks a strategy that has worked
              for learners like you, then writes the lesson at your level.
            </p>
          </div>
          <button onClick={() => generate(false)} disabled={generating} className="btn-primary px-6 py-3">
            {generating ? <><Spinner /> Preparing lesson…</> : <><Sparkles className="h-4 w-4" /> Generate lesson</>}
          </button>
        </div>
      ) : (
        <div className="grid gap-8 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="min-w-0 space-y-8">
            <LessonViewer lesson={lesson} topic={topic} onTryCode={tryCode}
              onRegenerate={() => generate(true)} regenerating={generating} />
            <div ref={playgroundRef} className="scroll-mt-8">
              <CodePlayground topicName={topic.name} topicId={topic.id} seed={seed} />
            </div>
          </div>
          <aside className="xl:sticky xl:top-8 xl:h-[calc(100vh-4rem)]">
            <TutorChat topic={topic} />
          </aside>
        </div>
      )}
    </div>
  )
}

export default Learn
