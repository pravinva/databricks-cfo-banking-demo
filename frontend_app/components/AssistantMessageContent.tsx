'use client'

import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface AssistantMessageContentProps {
  content: string
  isUser?: boolean
}

export default function AssistantMessageContent({
  content,
  isUser = false,
}: AssistantMessageContentProps) {
  const textClass = isUser ? 'text-white' : 'text-slate-800'
  const mutedClass = isUser ? 'text-blue-100' : 'text-slate-600'

  return (
    <div className={`text-sm leading-relaxed break-words ${textClass}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          h1: ({ children }) => (
            <h1 className={`text-base font-bold mt-1 mb-2 ${textClass}`}>{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className={`text-sm font-bold mt-1 mb-2 ${textClass}`}>{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className={`text-sm font-semibold mt-1 mb-2 ${textClass}`}>{children}</h3>
          ),
          p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
          ul: ({ children }) => <ul className="list-disc pl-5 mb-2 space-y-1">{children}</ul>,
          ol: ({ children }) => <ol className="list-decimal pl-5 mb-2 space-y-1">{children}</ol>,
          li: ({ children }) => <li className={`${textClass}`}>{children}</li>,
          strong: ({ children }) => <strong className={`font-semibold ${textClass}`}>{children}</strong>,
          em: ({ children }) => <em className={`italic ${textClass}`}>{children}</em>,
          code: ({ children, className }) => {
            if (className) {
              return (
                <code
                  className={`block rounded-md px-3 py-2 text-xs overflow-x-auto whitespace-pre ${isUser ? 'bg-blue-700 text-white' : 'bg-slate-900 text-slate-100'}`}
                >
                  {children}
                </code>
              )
            }

            return (
              <code
                className={`rounded px-1 py-0.5 text-xs ${isUser ? 'bg-blue-700 text-white' : 'bg-slate-200 text-slate-900'}`}
              >
                {children}
              </code>
            )
          },
          pre: ({ children }) => <div className="mb-2 last:mb-0">{children}</div>,
          blockquote: ({ children }) => (
            <blockquote className={`border-l-2 pl-3 my-2 italic ${isUser ? 'border-blue-300' : 'border-slate-300'} ${mutedClass}`}>
              {children}
            </blockquote>
          ),
          table: ({ children }) => (
            <div className="overflow-x-auto my-2">
              <table className={`min-w-full border text-xs tabular-nums ${isUser ? 'border-blue-300' : 'border-slate-300'}`}>{children}</table>
            </div>
          ),
          thead: ({ children }) => (
            <thead className={isUser ? 'bg-blue-700 text-white' : 'bg-slate-100 text-slate-800'}>{children}</thead>
          ),
          th: ({ children }) => (
            <th className={`border px-2 py-1 text-left font-semibold ${isUser ? 'border-blue-300' : 'border-slate-300'}`}>
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className={`border px-2 py-1 align-top ${isUser ? 'border-blue-300 text-blue-50' : 'border-slate-300 text-slate-700'}`}>
              {children}
            </td>
          ),
          hr: () => <hr className={`my-3 ${isUser ? 'border-blue-300' : 'border-slate-300'}`} />,
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
