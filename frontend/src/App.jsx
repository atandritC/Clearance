import { forwardRef, useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')
const DEMO_MODE_ENABLED = import.meta.env.VITE_DEMO_MODE !== 'false'

const startQuestions = [
  'How do I request time off?',
  'What should I do if my VPN is not connecting?',
  'How do I report a workplace concern?',
]

const iconPaths = {
  sparkle: <><path d="m12 3 1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8L12 3Z"/><path d="m19 15 .9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9L19 15Z"/></>,
  search: <><circle cx="10.8" cy="10.8" r="6.5"/><path d="m16 16 4.5 4.5"/></>,
  book: <><path d="M4 5.5A2.5 2.5 0 0 1 6.5 3H20v16H6.5A2.5 2.5 0 0 0 4 21.5v-16Z"/><path d="M4 17.5A2.5 2.5 0 0 1 6.5 15H20M8 7h8M8 10h8"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3.5 2"/></>,
  arrow: <><path d="M12 19V5M6 11l6-6 6 6"/></>,
  sun: <><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M4.9 4.9l1.4 1.4m11.4 11.4 1.4 1.4M2 12h2m16 0h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></>,
  moon: <path d="M20.8 14.2A8.5 8.5 0 0 1 9.8 3.2 8.8 8.8 0 1 0 20.8 14.2Z"/>,
  menu: <><path d="M4 7h16M4 12h16M4 17h16"/></>,
  close: <><path d="m6 6 12 12M18 6 6 18"/></>,
  down: <path d="m7 10 5 5 5-5"/>,
  file: <><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z"/><path d="M14 2v6h6M8 13h8M8 17h8"/></>,
  shield: <><path d="M12 22s8-4 8-11V5l-8-3-8 3v6c0 7 8 11 8 11Z"/><path d="m9 12 2 2 4-4"/></>,
  logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M12 3h6a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-6"/></>,
  chevron: <path d="m9 18 6-6-6-6"/>,
}

function Icon({ name, size = 18, className = '' }) {
  return <svg aria-hidden="true" className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{iconPaths[name]}</svg>
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(typeof body.detail === 'string' ? body.detail : 'The request could not be completed.')
  return body
}

function messageForError(error) {
  return error instanceof TypeError
    ? 'Clearance could not reach the API. Make sure the backend is running and try again.'
    : error?.message || 'Something went wrong. Please try again.'
}

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem('clearance-theme-mode') || 'system')
  const [systemTheme, setSystemTheme] = useState(() => window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
  const [users, setUsers] = useState([])
  const [identity, setIdentity] = useState(null)
  const [mode, setMode] = useState(DEMO_MODE_ENABLED ? 'demo' : 'auth')
  const [token, setToken] = useState('')
  const [view, setView] = useState('ask')
  const [adminDocument, setAdminDocument] = useState('HR-005')
  const [adminVersion, setAdminVersion] = useState('1.0')
  const [adminUserId, setAdminUserId] = useState('')
  const [adminGrants, setAdminGrants] = useState([])
  const [adminBusy, setAdminBusy] = useState(false)
  const [adminError, setAdminError] = useState('')
  const [adminSuccess, setAdminSuccess] = useState('')
  const [menuOpen, setMenuOpen] = useState(false)
  const [mobileNavOpen, setMobileNavOpen] = useState(false)
  const [loginOpen, setLoginOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [allowTicket, setAllowTicket] = useState(false)
  const [messages, setMessages] = useState([])
  const [busy, setBusy] = useState(false)
  const [bannerError, setBannerError] = useState('')
  const [loginEmail, setLoginEmail] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [loginError, setLoginError] = useState('')
  const [loginBusy, setLoginBusy] = useState(false)
  const inputRef = useRef(null)
  const chatEndRef = useRef(null)
  const activeTheme = theme === 'system' ? systemTheme : theme

  useEffect(() => {
    const preference = window.matchMedia('(prefers-color-scheme: dark)')
    const updateSystemTheme = (event) => setSystemTheme(event.matches ? 'dark' : 'light')
    preference.addEventListener('change', updateSystemTheme)
    return () => preference.removeEventListener('change', updateSystemTheme)
  }, [])

  useEffect(() => {
    document.documentElement.dataset.theme = activeTheme
    localStorage.setItem('clearance-theme-mode', theme)
  }, [activeTheme, theme])

  useEffect(() => {
    if (!DEMO_MODE_ENABLED) return
    let alive = true
    apiRequest('/demo/users').then((demoUsers) => {
      if (!alive) return
      setUsers(demoUsers)
      const storedId = Number(localStorage.getItem('clearance-demo-user'))
      const selected = demoUsers.find((user) => user.id === storedId)
        || demoUsers.find((user) => user.display_name === 'Mikasa Ackerman')
        || demoUsers[0]
      if (selected) setIdentity(selected)
    }).catch(() => {})
    return () => { alive = false }
  }, [])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [messages, busy])

  useEffect(() => {
    function onShortcut(event) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault()
        setView('ask')
        inputRef.current?.focus()
      }
    }
    window.addEventListener('keydown', onShortcut)
    return () => window.removeEventListener('keydown', onShortcut)
  }, [])

  const sources = useMemo(() => {
    const byChunk = new Map()
    messages.forEach((message) => (message.response?.citations || []).forEach((citation) => {
      byChunk.set(citation.chunk_id, citation)
    }))
    return [...byChunk.values()]
  }, [messages])
  const requests = useMemo(() => messages.flatMap((message) => (message.response?.tool_results || [])
    .flatMap((result) => {
      if (result.tool_name === 'create_it_ticket' && result.data?.ticket_number) {
        return [{ ...result.data, question: message.question, result_id: result.result_id }]
      }
      if (result.tool_name === 'list_my_it_tickets' && Array.isArray(result.data?.tickets)) {
        return result.data.tickets.map((ticket) => ({ ...ticket, question: message.question, result_id: `${result.result_id}-${ticket.ticket_number}` }))
      }
      return []
    })), [messages])
  const initials = (identity?.display_name || 'C').split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase()
  const pageTitle = view === 'ask' ? 'Ask Clearance' : view === 'sources' ? 'Sources' : view === 'requests' ? 'My requests' : 'Admin console'

  async function submitQuestion(value = question) {
    const clean = value.trim()
    if (clean.length < 3 || busy) return
    if (mode === 'demo' && !identity) {
      setBannerError('The demo account list is unavailable. Start the API and try again.')
      return
    }
    if (mode === 'auth' && !token) {
      setLoginOpen(true)
      return
    }
    const submittedAt = new Date().toISOString()
    setQuestion('')
    setBannerError('')
    setBusy(true)
    setView('ask')
    setMessages((current) => [...current, { question: clean, submittedAt }])
    try {
      const headers = mode === 'demo'
        ? { 'X-Demo-User-ID': String(identity.id) }
        : { Authorization: `Bearer ${token}` }
      const response = await apiRequest(mode === 'demo' ? '/demo/ask' : '/api/ask', {
        method: 'POST',
        headers,
        body: JSON.stringify({ question: clean, confirm_actions: allowTicket }),
      })
      setMessages((current) => current.map((item) => item.submittedAt === submittedAt ? { ...item, response } : item))
    } catch (error) {
      const reason = messageForError(error)
      setMessages((current) => current.map((item) => item.submittedAt === submittedAt ? { ...item, error: reason } : item))
    } finally {
      setBusy(false)
      setAllowTicket(false)
      inputRef.current?.focus()
    }
  }

  function chooseDemo(userId) {
    const next = users.find((user) => user.id === Number(userId))
    if (!next) return
    setIdentity(next)
    setMode('demo')
    setToken('')
    setMessages([])
    localStorage.setItem('clearance-demo-user', String(next.id))
    setMenuOpen(false)
    setMobileNavOpen(false)
  }

  async function signIn(event) {
    event.preventDefault()
    setLoginBusy(true)
    setLoginError('')
    try {
      const login = await apiRequest('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      })
      const user = await apiRequest('/auth/me', { headers: { Authorization: `Bearer ${login.access_token}` } })
      setIdentity(user)
      setToken(login.access_token)
      setMode('auth')
      setMessages([])
      setLoginPassword('')
      setLoginOpen(false)
      setMenuOpen(false)
      setView('ask')
    } catch (error) {
      setLoginError(messageForError(error))
    } finally {
      setLoginBusy(false)
    }
  }

  function signOut() {
    setToken('')
    setMode(DEMO_MODE_ENABLED ? 'demo' : 'auth')
    setIdentity(DEMO_MODE_ENABLED
      ? users.find((user) => user.id === Number(localStorage.getItem('clearance-demo-user'))) || users[0] || null
      : null)
    setMessages([])
    setView('ask')
    setMenuOpen(false)
  }

  async function loadAdminGrants(event, preserveFeedback = false) {
    event?.preventDefault()
    if (!token || !identity?.is_admin) return
    setAdminBusy(true)
    setAdminError('')
    if (!preserveFeedback) setAdminSuccess('')
    try {
      const grants = await apiRequest(`/api/admin/documents/${encodeURIComponent(adminDocument)}/versions/${encodeURIComponent(adminVersion)}/grants`, { headers: { Authorization: `Bearer ${token}` } })
      setAdminGrants(grants)
    } catch (error) {
      setAdminError(messageForError(error))
    } finally {
      setAdminBusy(false)
    }
  }

  async function createGrant(event) {
    event.preventDefault()
    if (!token || !identity?.is_admin || !adminUserId) return
    setAdminBusy(true)
    setAdminError('')
    setAdminSuccess('')
    try {
      await apiRequest(`/api/admin/documents/${encodeURIComponent(adminDocument)}/versions/${encodeURIComponent(adminVersion)}/grants`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ user_id: Number(adminUserId) }),
      })
      setAdminSuccess(`Access granted to user ${adminUserId}.`)
      setAdminUserId('')
      await loadAdminGrants(undefined, true)
    } catch (error) {
      setAdminError(messageForError(error))
      setAdminBusy(false)
    }
  }

  async function revokeGrant(userId) {
    if (!token || !identity?.is_admin) return
    setAdminBusy(true)
    setAdminError('')
    setAdminSuccess('')
    try {
      await apiRequest(`/api/admin/documents/${encodeURIComponent(adminDocument)}/versions/${encodeURIComponent(adminVersion)}/grants/${userId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      setAdminSuccess(`Access removed for user ${userId}.`)
      await loadAdminGrants(undefined, true)
    } catch (error) {
      setAdminError(messageForError(error))
      setAdminBusy(false)
    }
  }

  return <div className="app-shell">
    <aside className={`sidebar ${mobileNavOpen ? 'sidebar-open' : ''}`}>
      <div className="brand-lockup"><span className="brand-mark" aria-hidden="true">C</span><span className="brand-word">clearance</span><button className="icon-button mobile-close" aria-label="Close menu" onClick={() => setMobileNavOpen(false)}><Icon name="close" /></button></div>
      <button className="sidebar-search" onClick={() => { setView('ask'); inputRef.current?.focus(); setMobileNavOpen(false) }}><Icon name="search" size={16} /><span>Search your workspace</span><kbd>⌘ K</kbd></button>
      <div className="nav-label">Workspace</div>
      <nav className="main-nav" aria-label="Main navigation">
        <NavButton active={view === 'ask'} icon="sparkle" onClick={() => { setView('ask'); setMobileNavOpen(false) }}>Ask Clearance</NavButton>
        <NavButton active={view === 'sources'} icon="book" onClick={() => { setView('sources'); setMobileNavOpen(false) }}>Sources</NavButton>
        <NavButton active={view === 'requests'} icon="clock" onClick={() => { setView('requests'); setMobileNavOpen(false) }}>My requests</NavButton>
      </nav>
      <div className="sidebar-bottom">
        {mode === 'auth' && identity?.is_admin && <><div className="nav-label manage-label">Manage</div><nav className="manage-nav" aria-label="Administration"><NavButton active={view === 'admin'} icon="shield" onClick={() => { setView('admin'); setMobileNavOpen(false); setMenuOpen(false) }}>Admin console</NavButton></nav></>}
        <div className="privacy-note"><Icon name="shield" size={17} /><span>Your answers follow your account access.</span></div>
        <button className="profile-button" onClick={() => identity || mode === 'demo' ? setMenuOpen((open) => !open) : setLoginOpen(true)} aria-expanded={menuOpen}>
          <Avatar initials={initials} /><span className="profile-copy"><strong>{identity?.display_name || (mode === 'auth' ? 'Sign in to Clearance' : 'Connect to Clearance')}</strong><small>{identity?.department || (mode === 'auth' ? 'Use your account to continue' : 'Start the local API')}</small></span><Icon name="down" size={15} />
        </button>
        {menuOpen && <div className="profile-menu">
          <div className="menu-heading">{mode === 'demo' ? 'Viewing as' : 'Signed in as'}</div>
          {mode === 'demo' ? <label className="select-wrap"><span className="sr-only">Choose demo account</span><select value={identity?.id || ''} onChange={(event) => chooseDemo(event.target.value)}>{users.map((user) => <option key={user.id} value={user.id}>{user.display_name} · {user.role.replaceAll('_', ' ')}</option>)}</select><Icon name="down" size={15} /></label> : identity ? <p className="signed-in-label">{identity.display_name}<small>{identity.role?.replaceAll('_', ' ')}</small></p> : <p className="signed-in-label">Sign in to continue</p>}
          {mode === 'demo' ? <button className="menu-action" onClick={() => { setLoginOpen(true); setMenuOpen(false) }}>Sign in with a password <Icon name="chevron" size={15} /></button> : identity ? <button className="menu-action" onClick={signOut}><Icon name="logout" size={15} /> Sign out</button> : <button className="menu-action" onClick={() => { setLoginOpen(true); setMenuOpen(false) }}>Sign in with a password <Icon name="chevron" size={15} /></button>}
        </div>}
      </div>
    </aside>
    {mobileNavOpen && <button className="nav-backdrop" aria-label="Close navigation" onClick={() => setMobileNavOpen(false)} />}

    <main className="main-area">
      <header className="topbar">
        <div className="topbar-leading"><button className="icon-button mobile-menu" aria-label="Open menu" onClick={() => setMobileNavOpen(true)}><Icon name="menu" /></button><div className="breadcrumbs"><span>Workspace</span><Icon name="chevron" size={14} /><strong>{pageTitle}</strong></div></div>
        <div className="topbar-actions">{mode === 'demo' && <span className="demo-badge"><span />Demo account</span>}<button className="icon-button theme-toggle" aria-label={`Switch to ${activeTheme === 'light' ? 'dark' : 'light'} theme`} title={`Using ${theme === 'system' ? 'system' : 'manual'} theme`} onClick={() => setTheme(activeTheme === 'light' ? 'dark' : 'light')}><Icon name={activeTheme === 'light' ? 'moon' : 'sun'} size={18} /></button><button className="top-profile" aria-label="Open account menu" onClick={() => { setMenuOpen((open) => !open); if (window.innerWidth <= 700) setMobileNavOpen(true) }}><Avatar initials={initials} /></button></div>
      </header>

      <div className={`content-area ${view === 'ask' ? 'chat-view' : 'section-view'}`}>
        {view === 'ask' && <>
          {messages.length === 0 ? <Welcome identity={identity} onAsk={submitQuestion} /> : <Chat messages={messages} busy={busy} endRef={chatEndRef} />}
          {bannerError && <div className="error-banner" role="alert">{bannerError}</div>}
          <Composer ref={inputRef} question={question} setQuestion={setQuestion} busy={busy} allowTicket={allowTicket} setAllowTicket={setAllowTicket} onSubmit={() => submitQuestion()} />
          <p className="footnote">Clearance uses information your account is allowed to see. Check the cited source for details.</p>
        </>}
        {view === 'sources' && <SourcesView sources={sources} onBack={() => setView('ask')} />}
        {view === 'requests' && <RequestsView results={requests} onAsk={() => setView('ask')} />}
        {view === 'admin' && identity?.is_admin && <AdminView documentId={adminDocument} setDocumentId={setAdminDocument} version={adminVersion} setVersion={setAdminVersion} userId={adminUserId} setUserId={setAdminUserId} grants={adminGrants} busy={adminBusy} error={adminError} success={adminSuccess} onLoad={loadAdminGrants} onGrant={createGrant} onRevoke={revokeGrant} />}
      </div>
      <nav className="mobile-tabbar" aria-label="Mobile navigation"><NavButton active={view === 'ask'} icon="sparkle" onClick={() => setView('ask')}>Ask</NavButton><NavButton active={view === 'sources'} icon="book" onClick={() => setView('sources')}>Sources</NavButton><NavButton active={view === 'requests'} icon="clock" onClick={() => setView('requests')}>Requests</NavButton></nav>
    </main>

    {loginOpen && <div className="modal-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget) setLoginOpen(false) }}><section className="login-modal" role="dialog" aria-modal="true" aria-labelledby="login-title"><button className="icon-button modal-close" aria-label="Close sign in" onClick={() => setLoginOpen(false)}><Icon name="close" /></button><span className="modal-mark">C</span><p className="eyebrow">Welcome back</p><h2 id="login-title">Sign in to Clearance</h2><p className="modal-description">Use your company account to ask questions with your own access.</p><form className="login-form" onSubmit={signIn}><label>Email address<input type="email" autoComplete="username" required value={loginEmail} onChange={(event) => setLoginEmail(event.target.value)} placeholder="you@company.com" /></label><label>Password<input type="password" autoComplete="current-password" required value={loginPassword} onChange={(event) => setLoginPassword(event.target.value)} placeholder="Your password" /></label>{loginError && <p className="form-error" role="alert">{loginError}</p>}<button className="primary-button login-submit" disabled={loginBusy}>{loginBusy ? <span className="spinner" /> : 'Sign in'}</button></form><p className="modal-footnote"><Icon name="shield" size={15} /> Your session token stays in this browser tab.</p></section></div>}
  </div>
}

function NavButton({ active, icon, onClick, children }) {
  return <button className={`nav-item ${active ? 'active' : ''}`} aria-current={active ? 'page' : undefined} onClick={onClick}><Icon name={icon} size={18} /><span>{children}</span>{active && <span className="active-indicator" />}</button>
}

function Avatar({ initials }) {
  return <span className="avatar" aria-hidden="true">{initials}</span>
}

function Welcome({ identity, onAsk }) {
  return <section className="welcome-section">
    <div className="welcome-copy"><p className="eyebrow"><Icon name="sparkle" size={14} /> Your company,</p><h1>within reach.</h1><p className="welcome-subtitle">Ask a question. Get a clear answer with its sources.</p>{identity && <div className="welcome-context"><span className="context-dot" /> Answers are shaped by your {identity.department} access</div>}</div>
    <div className="welcome-illustration" aria-hidden="true"><div className="orb orb-one"/><div className="orb orb-two"/><div className="orbit-ring"/><div className="illustration-card card-back"><span/><i/><i/></div><div className="illustration-card card-front"><b>C</b><span/><i/><i/></div><div className="illustration-spark">✳</div></div>
    <div className="starter-block"><div className="section-heading"><span>Try asking</span><span className="heading-rule"/></div><div className="starter-list">{startQuestions.map((starter) => <button className="starter-card" key={starter} onClick={() => onAsk(starter)}><span className="starter-icon"><Icon name="sparkle" size={16}/></span><span>{starter}</span><Icon className="starter-arrow" name="arrow" size={16}/></button>)}</div></div>
    <div className="welcome-bottom"><span><Icon name="shield" size={15}/> Permission-aware answers</span><span>Fictional company workspace</span></div>
  </section>
}

function Chat({ messages, busy, endRef }) {
  return <div className="chat-thread" aria-live="polite"><div className="thread-heading"><p className="eyebrow">Your conversation</p><h1>Ask Clearance</h1><p>Answers include only sources available to your account.</p></div>{messages.map((message) => <article className="conversation-turn" key={message.submittedAt}><div className="question-row"><Avatar initials="You"/><div><span className="message-label">You</span><p>{message.question}</p></div></div><div className="answer-row"><div className="assistant-mark"><Icon name="sparkle" size={18}/></div><div className="answer-content"><span className="message-label">Clearance</span>{message.error ? <p className="inline-error" role="alert">{message.error}</p> : message.response && <><p className="answer-text">{message.response.answer}</p>{message.response.abstained && <p className="abstention-note">Try asking with more detail, or contact the team that owns this topic.</p>}{message.response.citations?.length > 0 && <div className="citation-list"><div className="citation-heading"><Icon name="book" size={15}/><span>Sources used</span></div>{message.response.citations.map((citation) => <details className="citation-card" key={`${citation.chunk_id}-${citation.version}`}><summary><span className="source-icon"><Icon name="file" size={15}/></span><span className="citation-copy"><strong>{citation.title}</strong><small>{citation.document_id} · v{citation.version} · {citation.department}</small></span><span className="source-tag">{citation.access_level || 'Source'}</span><Icon name="down" size={15}/></summary><div className="citation-excerpt">{citation.excerpt}</div><div className="citation-meta">Effective {citation.effective_date}{citation.chunk_index !== undefined && ` · Section ${citation.chunk_index + 1}`}</div></details>)}</div>}{message.response.tool_results?.map((result) => <ToolResult key={result.result_id} result={result}/>)}</>}</div></div></article>)}{busy && <div className="answer-row loading-row"><div className="assistant-mark"><Icon name="sparkle" size={18}/></div><div><span className="message-label">Clearance</span><p className="thinking"><span/><span/><span/> Finding an answer and checking its sources</p></div></div>}<div ref={endRef}/></div>
}

function ToolResult({ result }) {
  const data = result.data || {}
  if (Array.isArray(data.tickets)) return <div className="tool-result"><div className="tool-result-heading"><span className="tool-result-icon"><Icon name="clock" size={16}/></span><div><strong>Your recent IT requests</strong><small>Information from your account</small></div></div>{data.tickets.length ? data.tickets.map((ticket) => <div className="ticket-row" key={ticket.ticket_number}><span><b>{ticket.ticket_number}</b><small>{ticket.title}</small></span><span className={`status-pill status-${ticket.status}`}>{ticket.status}</span></div>) : <p className="tool-empty">You don’t have any IT requests yet.</p>}</div>
  if (data.ticket_number) return <div className="tool-result"><div className="tool-result-heading"><span className="tool-result-icon"><Icon name="shield" size={16}/></span><div><strong>IT request created</strong><small>{data.ticket_number}</small></div></div><div className="ticket-created-details"><b>{data.title}</b><span className={`status-pill status-${data.status}`}>{data.status}</span><span>{data.priority} priority</span></div></div>
  if (data.annual_days_remaining !== undefined) return <div className="tool-result balance-result"><div className="tool-result-heading"><span className="tool-result-icon"><Icon name="clock" size={16}/></span><div><strong>Your leave balance</strong><small>As of {data.as_of}</small></div></div><div className="balance-stats"><div><strong>{data.annual_days_remaining}</strong><span>annual days left</span></div><div><strong>{data.sick_days_remaining}</strong><span>sick days left</span></div></div></div>
  return null
}

const Composer = forwardRef(function Composer({ question, setQuestion, busy, allowTicket, setAllowTicket, onSubmit }, ref) {
  function onKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); onSubmit() }
  }
  return <form className="composer-wrap" onSubmit={(event) => { event.preventDefault(); onSubmit() }}><label className="sr-only" htmlFor="question-input">Ask a question</label><textarea ref={ref} id="question-input" rows="2" maxLength={500} value={question} onChange={(event) => setQuestion(event.target.value)} onKeyDown={onKeyDown} placeholder="Ask anything about your company…" disabled={busy}/><div className="composer-toolbar"><label className={`action-confirm ${allowTicket ? 'checked' : ''}`}><input type="checkbox" checked={allowTicket} onChange={(event) => setAllowTicket(event.target.checked)}/><span className="custom-check">{allowTicket ? '✓' : ''}</span><span>Allow creating an IT request</span><span className="confirm-info" title="Only needed when you ask Clearance to create an IT request.">i</span></label><div className="composer-controls"><span className="keyboard-hint">Enter to send · Shift + Enter for a new line</span><button className="send-button" aria-label="Send question" disabled={question.trim().length < 3 || busy}>{busy ? <span className="spinner"/> : <Icon name="arrow" size={18}/>}</button></div></div></form>
})

function SourcesView({ sources, onBack }) {
  return <section className="library-view"><div className="page-intro"><p className="eyebrow">Your workspace</p><h1>Sources</h1><p>Reference material shown in answers during this session.</p></div>{sources.length ? <div className="source-grid">{sources.map((source) => <article className="library-card" key={`${source.chunk_id}-${source.version}`}><div className="library-card-icon"><Icon name="file" size={18}/></div><div className="library-card-content"><span className="doc-id">{source.document_id} · Version {source.version}</span><h2>{source.title}</h2><p>{source.excerpt}</p><div className="library-card-footer"><span>{source.department}</span><span>Effective {source.effective_date}</span></div></div></article>)}</div> : <EmptyState icon="book" title="Sources will appear here" description="When Clearance answers a question, you can review the documents it used." action="Ask a question" onAction={onBack}/>}</section>
}

function RequestsView({ results, onAsk }) {
  return <section className="library-view"><div className="page-intro"><p className="eyebrow">Your activity</p><h1>My requests</h1><p>IT requests created or looked up through Clearance.</p></div>{results.length ? <div className="request-list">{results.map((result) => <article className="request-card" key={result.result_id}><div className="request-icon"><Icon name="clock" size={18}/></div><div className="request-main"><span className="doc-id">{result.ticket_number || 'Recent IT request'}</span><h2>{result.title || result.question}</h2><p>{result.description || `Opened through your Clearance session · ${result.priority || 'standard'} priority`}</p></div><span className={`status-pill status-${result.status || 'open'}`}>{result.status || 'open'}</span></article>)}</div> : <EmptyState icon="clock" title="No requests in this session" description="Ask Clearance to show your recent tickets or create an IT request. Ticket creation requires your confirmation." action="Ask Clearance" onAction={onAsk}/>}</section>
}

function AdminView({ documentId, setDocumentId, version, setVersion, userId, setUserId, grants, busy, error, success, onLoad, onGrant, onRevoke }) {
  return <section className="library-view admin-view"><div className="page-intro"><p className="eyebrow">Manage access</p><h1>Admin console</h1><p>Grant or remove access to an active restricted document version.</p></div><div className="admin-panel"><div className="admin-panel-heading"><span className="admin-panel-icon"><Icon name="shield" size={18}/></span><div><h2>Restricted document access</h2><p>Each grant is limited to one person and one document version.</p></div></div><form className="grant-form" onSubmit={onGrant}><label>Document ID<input required value={documentId} onChange={(event) => setDocumentId(event.target.value.trim().toUpperCase())} placeholder="HR-005"/></label><label>Version<input required value={version} onChange={(event) => setVersion(event.target.value)} placeholder="1.0"/></label><label>User ID<input required type="number" min="1" step="1" value={userId} onChange={(event) => setUserId(event.target.value)} placeholder="Enter employee ID"/></label><button className="primary-button" disabled={busy || !documentId || !version || !userId}>{busy ? <span className="spinner"/> : <Icon name="plus" size={16}/>} Grant access</button></form><div className="admin-toolbar"><div><h3>Current grants</h3><p>{documentId} · Version {version}</p></div><button className="secondary-button" disabled={busy} onClick={onLoad}>{busy ? <span className="spinner"/> : 'Refresh list'}</button></div>{error && <p className="admin-message error" role="alert">{error}</p>}{success && <p className="admin-message success" role="status">{success}</p>}{grants.length ? <div className="grant-list">{grants.map((grant) => <div className="grant-row" key={`${grant.user_id}-${grant.document_id}-${grant.version}`}><Avatar initials={`#${grant.user_id}`}/><div className="grant-user"><strong>User {grant.user_id}</strong><small>Granted {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium' }).format(new Date(grant.granted_at))}</small></div><button className="revoke-button" disabled={busy} onClick={() => onRevoke(grant.user_id)}>Remove access</button></div>)}</div> : <div className="grant-empty"><Icon name="shield" size={18}/><span>No grants loaded yet. Select a document version and refresh the list.</span></div>}</div><p className="admin-footnote"><Icon name="shield" size={15}/> The server checks your admin access for every change.</p></section>
}

function EmptyState({ icon, title, description, action, onAction }) {
  return <div className="empty-state"><span className="empty-icon"><Icon name={icon} size={22}/></span><h2>{title}</h2><p>{description}</p><button className="secondary-button" onClick={onAction}>{action}<Icon name="chevron" size={15}/></button></div>
}

export default App
