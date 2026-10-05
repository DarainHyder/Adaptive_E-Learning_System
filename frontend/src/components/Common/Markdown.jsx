import React from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import CodeBlock from './CodeBlock'

// Safe Markdown renderer (no raw HTML) with syntax-highlighted code blocks.
const Markdown = ({ children, className = '' }) => (
  <div className={`markdown ${className}`}>
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        code({ inline, className: cls, children: code, ...props }) {
          const match = /language-(\w+)/.exec(cls || '')
          const text = String(code).replace(/\n$/, '')
          if (!inline && (match || text.includes('\n'))) {
            return (
              <CodeBlock language={match ? match[1] : 'python'}>{text}</CodeBlock>
            )
          }
          return <code className="inline-code" {...props}>{code}</code>
        },
        pre: ({ children: c }) => <>{c}</>,
        a: ({ children: c, ...props }) => <a {...props} target="_blank" rel="noreferrer">{c}</a>,
      }}
    >
      {children || ''}
    </ReactMarkdown>
  </div>
)

export default Markdown
