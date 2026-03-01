import { useState, useRef, useEffect } from 'react'
import { useSettings } from '@/contexts/SettingsContext'
import { chatApi } from '@/services/api'

interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

interface ChatBoxProps {
  projectPath: string
  githubOwner: string
  githubRepo: string
}

export function ChatBox({ projectPath, githubOwner, githubRepo }: ChatBoxProps) {
  const { selectedProvider, selectedModel } = useSettings()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [issueIdx, setIssueIdx] = useState<number | null>(null)
  const [issueTitle, setIssueTitle] = useState('')
  const [issueBody, setIssueBody] = useState('')
  const [issueResult, setIssueResult] = useState<{ number: number; url: string } | null>(null)
  const [issueError, setIssueError] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function handleSend() {
    if (!input.trim() || !selectedProvider || !selectedModel || loading) return
    const userMsg: ChatMessage = { role: 'user', content: input.trim() }
    const newMessages = [...messages, userMsg]
    setMessages(newMessages)
    setInput('')
    setLoading(true)

    try {
      const { reply } = await chatApi.send({
        message: userMsg.content,
        project_path: projectPath || null,
        provider: selectedProvider,
        model: selectedModel,
        history: messages.map((m) => ({ role: m.role, content: m.content })),
      })
      setMessages([...newMessages, { role: 'assistant', content: reply }])
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : 'Failed to get response'
      setMessages([...newMessages, { role: 'assistant', content: `Error: ${errMsg}` }])
    } finally {
      setLoading(false)
    }
  }

  function openIssueForm(idx: number) {
    const msg = messages[idx]
    const firstLine = msg.content.split('\n')[0].slice(0, 100)
    setIssueIdx(idx)
    setIssueTitle(firstLine)
    setIssueBody(msg.content)
    setIssueResult(null)
    setIssueError('')
  }

  async function handleCreateIssue() {
    if (!issueTitle.trim() || !githubOwner || !githubRepo) return
    try {
      const result = await chatApi.createIssue({
        owner: githubOwner,
        repo: githubRepo,
        title: issueTitle,
        body: issueBody,
      })
      setIssueResult(result)
    } catch (err) {
      setIssueError(err instanceof Error ? err.message : 'Failed to create issue')
    }
  }

  return (
    <div className="chat-container">
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            {projectPath
              ? 'Ask questions about your loaded codebase...'
              : 'Load a project first for codebase-aware answers, or ask a general question.'}
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`chat-msg chat-msg-${msg.role}`}>
            <div className="chat-msg-label">{msg.role === 'user' ? 'You' : 'Assistant'}</div>
            <div className="chat-msg-content">{msg.content}</div>
            {msg.role === 'assistant' && githubOwner && githubRepo && (
              <button
                className="chat-issue-btn"
                onClick={() => openIssueForm(i)}
              >
                Create Issue
              </button>
            )}
            {issueIdx === i && (
              <div className="chat-issue-form" onClick={(e) => e.stopPropagation()}>
                {issueResult ? (
                  <div className="chat-issue-success">
                    Issue <a href={issueResult.url} target="_blank" rel="noopener noreferrer">#{issueResult.number}</a> created!
                    <button className="secondary" style={{ marginLeft: '0.5rem', fontSize: '0.75rem' }} onClick={() => setIssueIdx(null)}>Close</button>
                  </div>
                ) : (
                  <>
                    <input
                      value={issueTitle}
                      onChange={(e) => setIssueTitle(e.target.value)}
                      placeholder="Issue title"
                    />
                    <textarea
                      value={issueBody}
                      onChange={(e) => setIssueBody(e.target.value)}
                      rows={3}
                    />
                    {issueError && <div className="chat-issue-error">{issueError}</div>}
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button className="primary" onClick={handleCreateIssue} disabled={!issueTitle.trim()}>
                        Submit Issue
                      </button>
                      <button className="secondary" onClick={() => setIssueIdx(null)}>Cancel</button>
                    </div>
                  </>
                )}
              </div>
            )}
          </div>
        ))}
        {loading && (
          <div className="chat-msg chat-msg-assistant">
            <div className="chat-msg-label">Assistant</div>
            <div className="chat-msg-content chat-thinking">Thinking...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>
      <div className="chat-input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={selectedProvider ? 'Ask a question...' : 'Select a provider first'}
          disabled={!selectedProvider || loading}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault()
              handleSend()
            }
          }}
          rows={2}
        />
        <button
          className="primary"
          onClick={handleSend}
          disabled={!input.trim() || !selectedProvider || loading}
        >
          Send
        </button>
      </div>
    </div>
  )
}
