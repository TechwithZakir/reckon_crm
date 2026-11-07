/*
 * Aura tools dock for Frappe CRM.
 *
 * reckon_aura_theme renders this dock on Desk pages. The CRM is a separate
 * frappe-ui app, so it builds the same dock here, driven by the same Aura
 * Theme Settings (enable_theme, allow_user_override, enable_ai_bar) and the
 * same per-browser preferences ("aura:prefs"), so the two stay in step.
 *
 * Dependency-free on purpose: plain DOM, no Desk globals (frappe.boot, $, __).
 */

const PREF_KEY = 'aura:prefs'
const ACCENTS = ['violet', 'cyan', 'ember']
const API = '/api/method/'

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
    /* storage can be blocked; the dock still works for this page */
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

function isDark() {
  return document.documentElement.getAttribute('data-theme') === 'dark'
}

function applyAppearance(config) {
  const root = document.documentElement
  const prefs = config.allow_user_override ? readPrefs() : {}
  const accent = prefs.accent || config.accent || 'violet'
  root.setAttribute('data-aura-accent', accent)
  root.setAttribute('data-aura-density', prefs.density || config.density || 'comfortable')
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

function buildAskPanel(config) {
  const panel = document.createElement('div')
  panel.className = 'aura-ask-panel'
  panel.hidden = true
  panel.innerHTML = `
    <textarea placeholder="Ask about your CRM data…" aria-label="Question"></textarea>
    <div class="aura-ask-answer" aria-live="polite"></div>
    <button type="button" class="aura-ask-send">Ask</button>`
  const textarea = panel.querySelector('textarea')
  const answer = panel.querySelector('.aura-ask-answer')
  const send = panel.querySelector('.aura-ask-send')
  send.addEventListener('click', async () => {
    const question = textarea.value.trim()
    if (!question) return
    answer.textContent = 'Thinking…'
    send.disabled = true
    try {
      const reply = await call('reckon_aura_theme.api.ask', { post: true, params: { question } })
      answer.textContent = reply?.answer || 'No answer.'
    } catch {
      answer.textContent = 'Ask AI is unavailable right now. Check Aura Theme Settings → AI.'
    } finally {
      send.disabled = false
    }
  })
  textarea.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') send.click()
  })
  return panel
}

function buildDock(config) {
  const dock = document.createElement('div')
  dock.className = 'aura-tools aura-tools--dock'

  if (config.ai_bar) {
    const ask = document.createElement('button')
    ask.type = 'button'
    ask.className = 'aura-ask-trigger'
    ask.innerHTML = '<span class="aura-spark">✦</span><span>Ask AI</span>'
    ask.addEventListener('click', () => {
      const panel = dock.__askPanel
      panel.hidden = !panel.hidden
      if (!panel.hidden) panel.querySelector('textarea').focus()
    })
    dock.appendChild(ask)
  }

  if (config.allow_user_override) {
    const density = document.createElement('button')
    density.type = 'button'
    density.className = 'aura-icon-btn'
    density.title = 'Toggle density'
    density.setAttribute('aria-label', 'Toggle density')
    density.textContent = '≡'
    density.addEventListener('click', () => {
      const next = document.documentElement.getAttribute('data-aura-density') === 'compact' ? 'comfortable' : 'compact'
      writePrefs({ density: next })
      applyAppearance(config)
    })
    dock.appendChild(density)

    const accent = document.createElement('button')
    accent.type = 'button'
    accent.className = 'aura-icon-btn'
    accent.title = 'Change accent'
    accent.setAttribute('aria-label', 'Change accent')
    accent.innerHTML = '<span class="aura-swatch"></span>'
    accent.addEventListener('click', () => {
      const list = config.custom_accent ? [...ACCENTS, 'custom'] : ACCENTS
      const current = document.documentElement.getAttribute('data-aura-accent') || list[0]
      const next = list[(list.indexOf(current) + 1) % list.length]
      writePrefs({ accent: next })
      applyAppearance(config)
    })
    dock.appendChild(accent)
  }

  const mode = document.createElement('button')
  mode.type = 'button'
  mode.className = 'aura-icon-btn'
  mode.title = 'Light / dark'
  mode.setAttribute('aria-label', 'Light or dark mode')
  mode.textContent = isDark() ? '☀' : '☾'
  mode.addEventListener('click', () => {
    const next = isDark() ? 'light' : 'dark'
    setMode(next)
    mode.textContent = next === 'dark' ? '☀' : '☾'
  })
  dock.appendChild(mode)

  return dock
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

  const dock = buildDock(config)
  const panel = buildAskPanel(config)
  dock.__askPanel = panel
  document.body.appendChild(panel)
  document.body.appendChild(dock)
}
