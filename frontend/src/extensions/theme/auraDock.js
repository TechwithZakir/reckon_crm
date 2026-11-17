/*
 * Aura tools for Frappe CRM.
 *
 * The same Ask panel as reckon_aura_theme's Desk (aura_desk.js): same markup, classes, icons, chat, voice,
 * "Dock to right", shortcut and answers, styled by the same CSS (aura-desk-ui.css is copied from aura_desk.css,
 * see scripts/sync-aura-css.mjs). It is driven by Aura Theme Settings (enable_theme, allow_user_override,
 * enable_ai_bar) and shares the per-browser choices ("aura:prefs") and light/dark setting with the Desk.
 *
 * The tools sit in the CRM sidebar's bottom group, next to Help and Collapse, as CRM's own items do. If that
 * group is not on screen (other layouts), they float at the bottom right instead.
 *
 * Plain DOM, no Desk globals (frappe.boot, $, __).
 */

const PREF_KEY = 'aura:prefs'
const ACCENTS = ['violet', 'cyan', 'ember']
const API = '/api/method/'
const SIDEBAR_BOTTOM = '#app div.mt-auto.flex.flex-col.gap-1.pt-2'
const IC = {
  rows: 'M3 5h18M3 12h18M3 19h18',
  dense: 'M3 4h18M3 9h18M3 14h18M3 19h18',
  moon: 'M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z',
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4',
  x: 'M18 6 6 18M6 6l12 12',
  dock: 'M4 4h16v16H4zM10 4v16',
  newChat: 'M12 5v14M5 12h14',
  mic: 'M12 15a3 3 0 0 0 3-3V6a3 3 0 0 0-6 0v6a3 3 0 0 0 3 3zM19 11a7 7 0 0 1-14 0M12 18v4M8 22h8',
  send: 'M22 2 11 13M22 2 15 22 11 13 2 9 22 2',
  select: 'M8 5h12v14H8zM4 17V3h14',
}
const IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform || '')
const CHIPS = [
  'What needs my attention today?',
  'Summarise my open leads',
  'Which deals are closing this month?',
  'How do I add a field visit?',
]

const svg = (d, s = 16) =>
  `<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`

const escapeHtml = (v) =>
  String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

const formatAnswer = (text) =>
  escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^\s*[-•]\s+(.+)$/gm, '• $1')
    .replace(/\n/g, '<br>')

function readPrefs() {
  try {
    return JSON.parse(localStorage.getItem(PREF_KEY)) || {}
  } catch {
    return {}
  }
}

function writePrefs(patch) {
  try {
    localStorage.setItem(PREF_KEY, JSON.stringify({ ...readPrefs(), ...patch }))
  } catch {
    /* storage can be blocked; the tools still work for this page */
  }
}

async function call(method, { params = {}, post = false } = {}) {
  const headers = { 'X-Requested-With': 'XMLHttpRequest' }
  const init = { credentials: 'same-origin', headers }
  let url = API + method
  if (post) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    headers['X-Frappe-CSRF-Token'] = window.csrf_token || ''
    init.method = 'POST'
    init.body = new URLSearchParams(params)
  } else {
    const qs = new URLSearchParams(params).toString()
    if (qs) url += '?' + qs
  }
  const res = await fetch(url, init)
  if (!res.ok) throw new Error(`${method} failed: ${res.status}`)
  return (await res.json()).message
}

const isDark = () => document.documentElement.getAttribute('data-theme') === 'dark'

function applyAppearance(config) {
  const root = document.documentElement
  const prefs = config.allow_user_override ? readPrefs() : {}
  const accent = prefs.accent || config.accent || 'violet'
  root.setAttribute('data-aura', 'on')
  root.setAttribute('data-aura-accent', accent)
  root.setAttribute('data-aura-density', prefs.density || config.density || 'comfortable')
  root.setAttribute('data-aura-aurora', config.aurora_background === 0 ? 'off' : 'on')
  root.style.setProperty('--aura-blur', (config.glass_blur != null ? config.glass_blur : 18) + 'px')
  if (accent === 'custom' && config.custom_accent) {
    root.style.setProperty('--aura-accent', config.custom_accent)
    root.style.setProperty('--aura-accent-2', config.custom_accent_2 || config.custom_accent)
  } else {
    root.style.removeProperty('--aura-accent')
    root.style.removeProperty('--aura-accent-2')
  }
}

function setMode(next) {
  const root = document.documentElement
  root.setAttribute('data-theme', next)
  root.setAttribute('data-theme-mode', next)
  try {
    localStorage.setItem('theme', next)
  } catch {
    /* ignore */
  }
  // Persist on the User record, like the Desk toggle does.
  call('frappe.core.doctype.user.user.switch_theme', {
    post: true,
    params: { theme: next === 'dark' ? 'Dark' : 'Light' },
  }).catch(() => {})
}

// ---------------------------------------------------------------- the Ask panel (same as the Desk)

function buildAsk(config) {
  const brand = escapeHtml(config.brand_name || 'ReckonERP')
  const root = document.createElement('div')
  root.className = 'aura-ask-backdrop'
  root.setAttribute('role', 'presentation')
  root.innerHTML = `
    <section class="aura-ask" role="dialog" aria-modal="true" aria-label="Ask Aura AI">
      <header class="aura-ask-header">
        <div class="aura-ask-brand">
          <span class="aura-spark-badge">✦</span>
          <div><strong>Ask Aura AI</strong><small>CRM support assistant</small></div>
        </div>
        <div class="aura-ask-actions">
          <button type="button" class="aura-ask-tool" data-aura-ask-action="new-chat" title="New chat" aria-label="New chat">${svg(IC.newChat, 15)}</button>
          <button type="button" class="aura-ask-tool" data-aura-ask-action="dock" aria-pressed="false" title="Dock to right" aria-label="Dock to right">${svg(IC.dock, 15)}</button>
          <button type="button" class="aura-ask-tool" data-aura-ask-action="close" title="Close" aria-label="Close">${svg(IC.x, 15)}</button>
          <kbd>Esc</kbd>
        </div>
      </header>
      <div class="aura-ask-body">
        <div class="aura-ask-messages" role="log" aria-live="polite" aria-relevant="additions"></div>
      </div>
      <footer class="aura-ask-composer">
        <div class="aura-ask-compose">
          <textarea rows="1" maxlength="2000" autocomplete="off" spellcheck="true" placeholder="Message Aura AI…" aria-label="Message"></textarea>
          <div class="aura-ask-compose-actions">
            <button type="button" class="aura-ask-tool aura-ask-select-input" title="Select all input" aria-label="Select all input">${svg(IC.select, 15)}</button>
            <button type="button" class="aura-ask-tool aura-ask-voice" data-aura-ask-action="voice" aria-pressed="false" title="Start voice input" aria-label="Start voice input">${svg(IC.mic, 16)}</button>
            <button type="button" class="aura-ask-send" data-aura-ask-action="send" title="Send message" aria-label="Send message">${svg(IC.send, 16)}</button>
          </div>
        </div>
        <div class="aura-ask-disclaimer">Enter to send · Shift+Enter for a new line · AI can make mistakes</div>
      </footer>
    </section>`

  const textarea = root.querySelector('textarea')
  const messages = root.querySelector('.aura-ask-messages')
  const body = root.querySelector('.aura-ask-body')
  const state = { history: [], pending: false, recognition: null }

  const scrollDown = () => { body.scrollTop = body.scrollHeight }
  const resize = () => {
    textarea.style.height = 'auto'
    textarea.style.height = Math.min(textarea.scrollHeight, 140) + 'px'
  }
  const syncLayout = () => {
    const docked = root.classList.contains('is-open') && root.classList.contains('is-docked')
    document.body.classList.toggle('aura-ask-page-reflow', docked)
    root.querySelector('.aura-ask').setAttribute('aria-modal', docked ? 'false' : 'true')
  }
  const welcome = () => {
    messages.innerHTML = `
      <div class="aura-ask-welcome">
        <span class="aura-ask-welcome-icon">✦</span>
        <h2>How can I help with ${brand}?</h2>
        <p>Ask about your CRM: leads, deals, contacts, field visits, or what to do next.</p>
        <div class="aura-ask-chips">${CHIPS.map((c) => `<button type="button" class="aura-chip">${escapeHtml(c)}</button>`).join('')}</div>
      </div>`
  }
  const setBusy = (busy) => {
    state.pending = busy
    root.querySelectorAll('[data-aura-ask-action="send"], [data-aura-ask-action="new-chat"]').forEach((b) => { b.disabled = busy })
  }
  const addTurn = (role, content, kind) => {
    const turn = document.createElement('article')
    if (role === 'user') {
      turn.className = 'aura-chat-turn aura-chat-turn--user'
      turn.innerHTML = '<div class="aura-chat-bubble"></div>'
      turn.querySelector('.aura-chat-bubble').textContent = content
    } else {
      turn.className = 'aura-chat-turn aura-chat-turn--assistant'
      turn.innerHTML = `
        <div class="aura-chat-avatar">✦</div>
        <div class="aura-chat-message">
          <div class="aura-chat-label">${brand}</div>
          <div class="aura-chat-content"></div>
          <button type="button" class="aura-ask-tool aura-chat-select" data-aura-select-output title="Select all answer" aria-label="Select all answer">${svg(IC.select, 13)}</button>
        </div>`
      const holder = turn.querySelector('.aura-chat-content')
      if (kind === 'pending') holder.innerHTML = '<span class="aura-thinking"><i></i><i></i><i></i></span>'
      else if (kind === 'error') { holder.classList.add('is-error'); holder.textContent = content }
      else if (kind === 'note') { holder.classList.add('is-note'); holder.textContent = content }
      else holder.innerHTML = formatAnswer(content)
    }
    messages.appendChild(turn)
    scrollDown()
    return turn
  }

  const submit = async () => {
    if (state.pending) return
    const question = textarea.value.trim()
    if (!question) return
    messages.querySelector('.aura-ask-welcome')?.remove()
    addTurn('user', question)
    if (!config.ai_ready) {
      addTurn('assistant', 'AI answers are not set up yet. A System Manager can add a model and API key in Aura Theme Settings.', 'note')
      return
    }
    textarea.value = ''
    resize()
    const pending = addTurn('assistant', '', 'pending')
    setBusy(true)
    try {
      const reply = await call('reckon_aura_theme.api.ask', {
        post: true,
        params: { question, route: location.pathname, history: JSON.stringify(state.history.slice(-12)) },
      })
      const answer = (reply && reply.answer) || 'No answer.'
      pending.querySelector('.aura-chat-content').innerHTML = formatAnswer(answer)
      state.history = state.history.concat({ role: 'user', content: question }, { role: 'assistant', content: answer }).slice(-12)
    } catch (error) {
      const holder = pending.querySelector('.aura-chat-content')
      holder.classList.add('is-error')
      holder.textContent = 'Could not get an answer. Check Aura Theme Settings → AI.'
    }
    scrollDown()
    setBusy(false)
  }

  const close = () => {
    if (state.recognition) state.recognition.stop()
    root.classList.remove('is-open')
    syncLayout()
  }
  const open = () => {
    if (!config.ai_bar) return
    root.classList.add('is-open')
    syncLayout()
    setTimeout(() => textarea.focus(), 20)
  }
  const newChat = () => {
    if (state.pending) return
    state.history = []
    welcome()
    textarea.value = ''
    resize()
    textarea.focus()
  }
  const toggleDock = () => {
    const docked = root.classList.toggle('is-docked')
    const button = root.querySelector('[data-aura-ask-action="dock"]')
    button.setAttribute('aria-pressed', docked ? 'true' : 'false')
    button.setAttribute('title', docked ? 'Undock' : 'Dock to right')
    button.setAttribute('aria-label', docked ? 'Undock' : 'Dock to right')
    syncLayout()
  }
  const toggleVoice = () => {
    if (state.recognition) { state.recognition.stop(); return }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const voice = root.querySelector('.aura-ask-voice')
    if (!Recognition) { voice.title = 'Voice input is not supported in this browser'; return }
    const recognition = new Recognition()
    const lang = document.documentElement.lang || 'en'
    recognition.lang = lang.startsWith('bn') ? 'bn-BD' : lang.startsWith('en') ? 'en-US' : lang
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (event) => {
      const heard = Array.from(event.results).filter((r) => r.isFinal).map((r) => r[0].transcript).join(' ').trim()
      if (heard) { textarea.value = (textarea.value.trim() + ' ' + heard).trim(); resize() }
    }
    recognition.onend = () => {
      if (state.recognition === recognition) state.recognition = null
      voice.classList.remove('is-listening')
      voice.setAttribute('aria-pressed', 'false')
    }
    state.recognition = recognition
    voice.classList.add('is-listening')
    voice.setAttribute('aria-pressed', 'true')
    try { recognition.start() } catch { state.recognition = null; voice.classList.remove('is-listening') }
  }

  // A press on the empty backdrop closes the panel; nothing else is cancelled, so text can be selected and the
  // message box focused with the mouse.
  root.addEventListener('mousedown', (event) => { if (event.target === root) close() })
  root.addEventListener('mousedown', (event) => {
    const compose = event.target.closest('.aura-ask-compose')
    if (compose && event.target !== textarea && !event.target.closest('button')) {
      event.preventDefault()
      textarea.focus()
    }
  })
  root.addEventListener('click', (event) => {
    const action = event.target.closest('[data-aura-ask-action]')?.getAttribute('data-aura-ask-action')
    if (action === 'dock') toggleDock()
    else if (action === 'new-chat') newChat()
    else if (action === 'voice') toggleVoice()
    else if (action === 'send') submit()
    else if (action === 'close') close()
    else if (event.target.closest('.aura-ask-select-input')) { textarea.focus(); textarea.select() }
    else if (event.target.closest('[data-aura-select-output]')) {
      const answer = event.target.closest('.aura-chat-turn')?.querySelector('.aura-chat-content')
      if (answer) {
        const range = document.createRange()
        range.selectNodeContents(answer)
        const selection = window.getSelection()
        selection.removeAllRanges()
        selection.addRange(range)
      }
    } else if (event.target.closest('.aura-chip')) {
      textarea.value = event.target.closest('.aura-chip').textContent
      submit()
    }
  })
  root.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') close()
  })
  textarea.addEventListener('input', resize)
  textarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); submit() }
  })

  welcome()
  document.body.appendChild(root)
  return { open, close, isOpen: () => root.classList.contains('is-open') }
}

// ---------------------------------------------------------------- the tools

function buildTools(config, ask, sidebar) {
  const tools = document.createElement('div')
  tools.className = 'aura-tools ' + (sidebar ? 'aura-tools--sidebar' : 'aura-tools--dock')
  const parts = []
  if (config.ai_bar) {
    parts.push(
      `<button type="button" class="aura-ask-trigger" data-aura-action="ask" title="Ask Aura AI">` +
        `<span class="aura-spark">✦</span><span class="aura-ask-text">Ask Aura AI</span>` +
        `<kbd>${IS_MAC ? '⌘J' : 'Ctrl J'}</kbd></button>`,
    )
  }
  const icons = []
  if (config.allow_user_override) {
    icons.push(`<button type="button" class="aura-icon-btn" data-aura-action="density" title="Toggle density"></button>`)
    icons.push(`<button type="button" class="aura-icon-btn" data-aura-action="accent" title="Change accent"><span class="aura-swatch"></span></button>`)
  }
  icons.push(`<button type="button" class="aura-icon-btn" data-aura-action="mode" title="Light / dark"></button>`)
  parts.push(sidebar ? `<div class="aura-tools-row">${icons.join('')}</div>` : icons.join(''))
  tools.innerHTML = parts.join('')

  const sync = () => {
    const mode = tools.querySelector('[data-aura-action="mode"]')
    if (mode) mode.innerHTML = svg(isDark() ? IC.sun : IC.moon)
    const density = tools.querySelector('[data-aura-action="density"]')
    if (density) density.innerHTML = svg(document.documentElement.getAttribute('data-aura-density') === 'compact' ? IC.dense : IC.rows)
  }

  tools.addEventListener('click', (event) => {
    const button = event.target.closest('[data-aura-action]')
    if (!button) return
    const action = button.getAttribute('data-aura-action')
    if (action === 'ask') ask.open()
    else if (action === 'density') {
      writePrefs({ density: document.documentElement.getAttribute('data-aura-density') === 'compact' ? 'comfortable' : 'compact' })
      applyAppearance(config)
    } else if (action === 'accent') {
      const list = config.custom_accent ? [...ACCENTS, 'custom'] : ACCENTS
      const current = document.documentElement.getAttribute('data-aura-accent') || list[0]
      writePrefs({ accent: list[(list.indexOf(current) + 1) % list.length] })
      applyAppearance(config)
    } else if (action === 'mode') setMode(isDark() ? 'light' : 'dark')
    sync()
  })
  sync()
  return tools
}

// Put the tools at the top of the CRM sidebar's bottom group (above Help and Collapse), and keep them there
// while Vue re-renders the sidebar (collapse, route changes). Falls back to the floating dock after a while.
function placeTools(config, ask) {
  let floating = null
  let inSidebar = null
  const attach = () => {
    const group = document.querySelector(SIDEBAR_BOTTOM)
    if (!group) return false
    if (!inSidebar) inSidebar = buildTools(config, ask, true)
    if (inSidebar.parentElement !== group) group.insertBefore(inSidebar, group.firstChild)
    // Collapsed sidebar: icons only.
    inSidebar.classList.toggle('is-collapsed', group.getBoundingClientRect().width < 120)
    if (floating) { floating.remove(); floating = null }
    return true
  }
  let queued = false
  const observer = new MutationObserver(() => {
    if (queued) return
    queued = true
    requestAnimationFrame(() => { queued = false; attach() })  // Vue re-renders often: once per frame is enough
  })
  observer.observe(document.body, { childList: true, subtree: true })
  window.addEventListener('resize', attach)
  if (!attach()) {
    setTimeout(() => {
      if (!attach() && !floating) {
        floating = buildTools(config, ask, false)
        document.body.appendChild(floating)
      }
    }, 8000)
  }
}

export async function mountAuraDock() {
  let config
  try {
    config = await call('reckon_crm.api.theme.dock_config')
  } catch {
    return // Aura not installed on this site: keep the CRM as it is.
  }
  if (!config || config.enabled === 0) return

  applyAppearance(config)
  const ask = buildAsk(config)
  placeTools(config, ask)

  // Same shortcut as the Desk: Ctrl/⌘ + J opens Ask Aura AI.
  document.addEventListener('keydown', (event) => {
    if (!config.ai_bar) return
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'j') {
      event.preventDefault()
      ask.isOpen() ? ask.close() : ask.open()
    }
  })
}
