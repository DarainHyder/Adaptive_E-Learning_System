import React from 'react'
import { PrismLight as SyntaxHighlighter } from 'react-syntax-highlighter'
import vscDarkPlus from 'react-syntax-highlighter/dist/esm/styles/prism/vsc-dark-plus'
import python from 'react-syntax-highlighter/dist/esm/languages/prism/python'
import javascript from 'react-syntax-highlighter/dist/esm/languages/prism/javascript'
import jsx from 'react-syntax-highlighter/dist/esm/languages/prism/jsx'
import sql from 'react-syntax-highlighter/dist/esm/languages/prism/sql'
import bash from 'react-syntax-highlighter/dist/esm/languages/prism/bash'
import json from 'react-syntax-highlighter/dist/esm/languages/prism/json'
import markup from 'react-syntax-highlighter/dist/esm/languages/prism/markup'
import css from 'react-syntax-highlighter/dist/esm/languages/prism/css'

// Register only the languages lessons use (the full Prism bundle is ~1 MB)
const LANGS = { python, javascript, jsx, sql, bash, json, markup, css }
Object.entries(LANGS).forEach(([name, lang]) => SyntaxHighlighter.registerLanguage(name, lang))
const ALIASES = { py: 'python', js: 'javascript', html: 'markup', xml: 'markup', sh: 'bash', shell: 'bash' }

const CodeBlock = ({ language = 'python', children }) => (
  <SyntaxHighlighter
    language={ALIASES[language] || language}
    style={vscDarkPlus}
    customStyle={{ margin: '1rem 0', borderRadius: '0.875rem', padding: '1.25rem', fontSize: '0.8125rem',
      background: '#0a0a0b', border: '1px solid #27272d', lineHeight: 1.7 }}
    codeTagProps={{ style: { fontFamily: '"JetBrains Mono", ui-monospace, monospace' } }}
  >
    {children}
  </SyntaxHighlighter>
)

export default CodeBlock
