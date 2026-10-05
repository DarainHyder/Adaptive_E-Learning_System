import React from 'react'
import { Info } from 'lucide-react'

const REPO_URL = 'https://github.com/DarainHyder/Adaptive_E-Learning_System'

// Shown once, on the sign-in page: this deployment is a portfolio demo, not a production service.
const DemoNotice = () => (
  <aside className="mt-8 rounded-xl border border-gold-500/25 bg-gold-400/[0.04] p-4 text-xs leading-5 text-fg-muted" role="note">
    <p className="mb-2 flex items-center gap-2 text-sm font-medium text-gold-200">
      <Info className="h-4 w-4 text-gold-400" /> Portfolio demo, not a production service
    </p>
    <ul className="ml-6 list-disc space-y-1.5 marker:text-gold-500/60">
      <li>
        The demo's Gemini API quota has run out, so AI lessons and tutor replies fall back to built-in content.
        For the full experience, clone the{' '}
        <a href={REPO_URL} target="_blank" rel="noreferrer" className="link-gold underline underline-offset-2">project on GitHub</a>,
        add your own Gemini API key and run or deploy it yourself.
      </li>
      <li>
        The backend runs on Hugging Face's free tier, so data is not persistent: accounts and progress may be
        reset whenever the server restarts or sleeps. The first request after a quiet period can take about 30 seconds.
      </li>
    </ul>
  </aside>
)

export default DemoNotice
