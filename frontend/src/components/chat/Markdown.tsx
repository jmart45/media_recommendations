import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Renders assistant messages as real Markdown (replacing the old regex-based
 *  converter), with styling tuned to the dark theme. */
export default function Markdown({ children }: { children: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        p: ({ node: _n, ...props }) => <p className="mb-2 last:mb-0" {...props} />,
        ul: ({ node: _n, ...props }) => <ul className="my-1.5 list-disc pl-5" {...props} />,
        ol: ({ node: _n, ...props }) => <ol className="my-1.5 list-decimal pl-5" {...props} />,
        li: ({ node: _n, ...props }) => <li className="my-0.5" {...props} />,
        strong: ({ node: _n, ...props }) => <strong className="text-accent2" {...props} />,
        code: ({ node: _n, ...props }) => (
          <code className="rounded bg-tool px-1.5 py-px text-[0.85em]" {...props} />
        ),
        a: ({ node: _n, ...props }) => (
          <a className="text-accent2 underline" target="_blank" rel="noreferrer" {...props} />
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
