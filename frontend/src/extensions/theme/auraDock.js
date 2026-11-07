/*
 * Aura tools dock for Frappe CRM.
 *
 * The same dock as reckon_aura_theme's Desk dock: same markup, classes, SVG
 * icons, shortcut and Ask AI modal, styled by aura-desk-ui.css. It is driven by
 * the Aura Theme Settings (enable_theme, allow_user_override, enable_ai_bar)
 * and shares the per-browser choices ("aura:prefs") and light/dark setting.
 *
 * Plain DOM, no Desk globals (frappe.boot, $, __).
 */

const PREF_KEY = 'aura:prefs'
const ACCENTS = ['violet', 'cyan', 'ember']
const API = '/api/method/'
const IC = {
  rows: 'M3 5h18M3 12h18M3 19h18',
  dense: 'M3 4h18M3 9h18M3 14h18M3 19h18',
  moon: 'M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z',
  sun: 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M6.3 17.7l-1.4 1.4M19.1 4.9l-1.4 1.4',
}
const IS_MAC = /Mac|iPhone|iPad/.test(navigator.platform || '')

const svg = (d, s = 16) =>
  `<svg viewBox="0 0 24 24" width="${s}" height="${s}" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${d}"/></svg>`

const escapeHtml = (v) =>
  String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])

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

function buildAsk(config) {
  const brand = escapeHtml(config.brand_name || 'ReckonERP')
  const backdrop = document.createElement('div')
  backdrop.className = 'aura-ask-backdrop'
  backdrop.setAttribute('role', 'presentation')
  backdrop.innerHTML = `
    <div class="aura-ask" role="dialog" aria-modal="true" aria-label="Ask AI">
      <div class="aura-ask-input">
        <span class="aura-spark-badge">✦</span>
        <input type="text" autocomplete="off" spellcheck="false"
          placeholder="Ask ${brand} AI about your CRM…">
        <kbd>Esc</kbd>
      </div>
      <div class="aura-ask-body"></div>
    </div>`
  const input = backdrop.querySelector('input')
  const body = backdrop.querySelector('.aura-ask-body')

  const close = () => backdrop.classList.remove('is-open')
  const open = () => {
    backdrop.classList.add('is-open')
    input.focus()
  }

  const submit = async () => {
    const question = input.value.trim()
    if (!question) return
    body.innerHTML = '<div class="aura-answer">Thinking…</div>'
    try {
      const reply = await call('reckon_aura_theme.api.ask', { post: true, params: { question } })
      body.innerHTML = `<div class="aura-answer">${escapeHtml(reply?.answer || 'No answer.')}</div>`
    } catch {
      body.innerHTML = '<div class="aura-answer is-error">Ask AI is unavailable. Check Aura Theme Settings → AI.</div>'
    }
  }

  backdrop.addEventListener('mousedown', (event) => event.target === backdrop && close())
  backdrop.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') close()
    if (event.key === 'Enter' && document.activeElement === input) submit()
  })

  document.body.appendChild(backdrop)
  return { open, close, isOpen: () => backdrop.classList.contains('is-open') }
}

function buildDock(config, ask) {
  const dock = document.createElement('div')
  dock.className = 'aura-tools aura-tools--dock'
  const parts = []
  if (config.ai_bar) {
    parts.push(
      `<button type="button" class="aura-ask-trigger" data-aura-action="ask" title="Ask AI">` +
        `<span class="aura-spark">✦</span><span class="aura-ask-text">Ask AI</span>` +
        `<kbd>${IS_MAC ? '⌘J' : 'Ctrl J'}</kbd></button>`,
    )
  }
  if (config.allow_user_override) {
    parts.push(`<button type="button" class="aura-icon-btn" data-aura-action="density" title="Toggle density"></button>`)
    parts.push(`<button type="button" class="aura-icon-btn" data-aura-action="accent" title="Change accent"><span class="aura-swatch"></span></button>`)
  }
  parts.push(`<button type="button" class="aura-icon-btn" data-aura-action="mode" title="Light / dark"></button>`)
  dock.innerHTML = parts.join('')

  const sync = () => {
    const mode = dock.querySelector('[data-aura-action="mode"]')
    if (mode) mode.innerHTML = svg(isDark() ? IC.sun : IC.moon)
    const density = dock.querySelector('[data-aura-action="density"]')
    if (density) {
      density.innerHTML = svg(document.documentElement.getAttribute('data-aura-density') === 'compact' ? IC.dense : IC.rows)
    }
  }

  dock.addEventListener('click', (event) => {
    const button = event.target.closest('[data-aura-action]')
    if (!button) return
    const action = button.getAttribute('data-aura-action')
    if (action === 'ask') ask.open()
    else if (action === 'density') {
      const next = document.documentElement.getAttribute('data-aura-density') === 'compact' ? 'comfortable' : 'compact'
      writePrefs({ density: next })
      applyAppearance(config)
    } else if (action === 'accent') {
      const list = config.custom_accent ? [...ACCENTS, 'custom'] : ACCENTS
      const current = document.documentElement.getAttribute('data-aura-accent') || list[0]
      writePrefs({ accent: list[(list.indexOf(current) + 1) % list.length] })
      applyAppearance(config)
    } else if (action === 'mode') {
      setMode(isDark() ? 'light' : 'dark')
    }
    sync()
  })

  sync()
  return { dock, sync }
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
  const { dock } = buildDock(config, ask)
  document.body.appendChild(dock)

  // Same shortcut as the Desk: Ctrl/⌘ + J opens Ask AI.
  document.addEventListener('keydown', (event) => {
    if (!config.ai_bar) return
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'j') {
      event.preventDefault()
      ask.isOpen() ? ask.close() : ask.open()
    }
  })
}
