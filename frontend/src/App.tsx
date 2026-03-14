import { useEffect, useState } from 'react'
import './style.css'

type Role = 'user' | 'bot'

interface Message {
  id: number
  role: Role
  text: string
  keywords?: string[]
  sourceTitle?: string
  sourceUrl?: string | null
}

const API_URL = 'http://localhost:8000/api/chat'
const KB_STATUS_URL = 'http://localhost:8000/kb/hash'

interface KnowledgeStatus {
  current_hash?: string | null
  ledger_hash?: string | null
  expected_hash?: string | null
  valid: boolean
}

export function App() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: 0,
      role: 'bot',
      text: 'Hello! I am your public health assistant. Ask me about diseases, symptoms, and prevention. This information is for awareness only and does not replace a doctor.',
    },
  ])
  const [input, setInput] = useState('')
  const [language, setLanguage] = useState('en')
  const [loading, setLoading] = useState(false)
  const [kbStatus, setKbStatus] = useState<KnowledgeStatus | null>(null)
  const [hasLoadedFromStorage, setHasLoadedFromStorage] = useState(false)

  // Load previous conversation and settings from localStorage
  useEffect(() => {
    try {
      const stored = window.localStorage.getItem('phc_messages')
      const storedLang = window.localStorage.getItem('phc_language')
      if (stored) {
        const parsed: Message[] = JSON.parse(stored)
        if (parsed.length > 0) {
          setMessages(parsed)
        }
      }
      if (storedLang) {
        setLanguage(storedLang)
      }
      setHasLoadedFromStorage(true)
    } catch {
      // ignore corrupted storage
    }
  }, [])

  // Persist conversation and language on every change
  useEffect(() => {
    if (!hasLoadedFromStorage) return
    try {
      window.localStorage.setItem('phc_messages', JSON.stringify(messages))
      window.localStorage.setItem('phc_language', language)
    } catch {
      // ignore write errors
    }
  }, [messages, language, hasLoadedFromStorage])

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const res = await fetch(KB_STATUS_URL)
        if (!res.ok) return
        const data = await res.json()
        setKbStatus(data)
      } catch {
        setKbStatus(null)
      }
    }
    fetchStatus()
  }, [])

  const recentQuestions = [...messages]
    .filter(m => m.role === 'user')
    .slice(-10)
    .reverse()

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: Date.now(),
      role: 'user',
      text: input.trim(),
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage.text, language }),
      })

      if (!res.ok) {
        throw new Error('API error')
      }

      const data = await res.json()
      const botMessage: Message = {
        id: Date.now() + 1,
        role: 'bot',
        text: data.answer,
        keywords: data.important_keywords,
        sourceTitle: data.source_title,
        sourceUrl: data.source_url,
      }
      setMessages(prev => [...prev, botMessage])
    } catch (err) {
      const errorMessage: Message = {
        id: Date.now() + 2,
        role: 'bot',
        text: 'Sorry, I had trouble reaching the health information server. Please make sure the backend is running and try again.',
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const renderWithHighlights = (text: string, keywords?: string[]) => {
    if (!keywords || keywords.length === 0) return text

    const pattern = new RegExp(`(${keywords.join('|')})`, 'gi')
    const parts = text.split(pattern)

    return parts.map((part, i) => {
      const isKeyword = keywords.some(k => k.toLowerCase() === part.toLowerCase())
      if (isKeyword) {
        return (
          <mark key={i} className="keyword">
            {part}
          </mark>
        )
      }
      return <span key={i}>{part}</span>
    })
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <h1>Secure Public Health Chatbot</h1>
          <p>Reliable, verified health awareness assistant (not a medical diagnosis tool).</p>
        </div>
        {kbStatus && (
          <div className={`kb-chip ${kbStatus.valid ? 'ok' : 'bad'}`}>
            {kbStatus.valid ? 'Knowledge base: Verified' : 'Knowledge base: Verification failed'}
          </div>
        )}
        <div className="language-select">
          <label>
            Language:
            <select
              value={language}
              onChange={e => setLanguage(e.target.value)}
            >
              <option value="en">English</option>
              <option value="hi">Hindi (text in English)</option>
            </select>
          </label>
        </div>
      </header>

      <main className="layout">
        <section className="chat-container">
          <div className="messages">
            {messages.map(msg => (
              <div
                key={msg.id}
                className={`message ${msg.role === 'user' ? 'user' : 'bot'}`}
              >
                <div className="bubble">
                  {msg.role === 'bot'
                    ? renderWithHighlights(msg.text, msg.keywords)
                    : msg.text}
                  {msg.role === 'bot' && msg.sourceTitle && (
                    <div className="source">
                      Source:{' '}
                      {msg.sourceUrl ? (
                        <a href={msg.sourceUrl} target="_blank" rel="noreferrer">
                          {msg.sourceTitle}
                        </a>
                      ) : (
                        msg.sourceTitle
                      )}
                    </div>
                  )}
                  {msg.role === 'bot' && msg.keywords && msg.keywords.length > 0 && (
                    <div className="keywords-list">
                      Important factors:{' '}
                      {msg.keywords.map(k => (
                        <span key={k} className="keyword-chip">
                          {k}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="message bot">
                <div className="bubble typing">Thinking…</div>
              </div>
            )}
          </div>

          <form className="input-bar" onSubmit={sendMessage}>
            <input
              type="text"
              placeholder="Type your health question here…"
              value={input}
              onChange={e => setInput(e.target.value)}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </section>

        <aside className="info-panel">
          <section className="info-card">
            <h2>System pipeline</h2>
            <ul className="pill-list">
              <li>NLP preprocessing</li>
              <li>TF-IDF vectorization</li>
              <li>ML classifier (Logistic Regression)</li>
              <li>Explainable AI (keyword highlights)</li>
            </ul>
          </section>

          <section className="info-card">
            <h2>Knowledge base topics</h2>
            <ul className="pill-list">
              <li>General hygiene & handwashing</li>
              <li>Respiratory illness & COVID-19</li>
              <li>Dengue & mosquito-borne disease</li>
              <li>Diabetes & lifestyle</li>
              <li>Hypertension & heart health</li>
            </ul>
          </section>

          <section className="info-card">
            <h2>Recent questions</h2>
            {recentQuestions.length === 0 ? (
              <p className="muted">Your recent questions will appear here.</p>
            ) : (
              <ul className="recent-list">
                {recentQuestions.map(q => (
                  <li
                    key={q.id}
                    onClick={() => setInput(q.text)}
                    title="Click to ask again"
                  >
                    {q.text}
                  </li>
                ))}
              </ul>
            )}
          </section>

          <section className="info-card">
            <h2>Safety notice</h2>
            <p className="muted">
              This chatbot is intended for learning and awareness only. It does not provide
              medical diagnosis or treatment. For urgent or serious symptoms, contact your
              local emergency number or a qualified healthcare professional immediately.
            </p>
          </section>
        </aside>
      </main>

      <footer className="app-footer">
        This chatbot provides general health awareness information only. For any emergency or
        personal medical advice, please contact a qualified healthcare professional.
      </footer>
    </div>
  )
}

