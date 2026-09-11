const stores = { tabs: new Map(), routes: new Map(), sidebar: new Map(), actions: new Map() }

function required(value, field) {
  if (typeof value !== 'string' || !value.trim()) throw new TypeError(`${field} is required`)
}

export function register(kind, entry) {
  if (!entry || typeof entry !== 'object') throw new TypeError('Extension must be an object')
  required(entry.name, 'name')
  if (kind === 'tabs' || kind === 'actions') {
    if (!['CRM Lead', 'CRM Deal', 'CRM Organization'].includes(entry.doctype)) {
      throw new TypeError('Unsupported CRM doctype')
    }
  }
  if (kind === 'tabs' || kind === 'routes') {
    if (!entry.component) throw new TypeError('component is required')
  }
  if (kind === 'routes' && (!/^\/[a-z0-9-]+(?:\/[a-z0-9-]+)*$/.test(entry.path) || entry.path.startsWith('/crm'))) {
    throw new TypeError('Route path must be relative to the /crm router base, e.g. /visits')
  }
  if (kind === 'sidebar') {
    required(entry.section, 'section')
    required(entry.label, 'label')
    required(entry.routeName, 'routeName')
  }
  if (kind === 'actions' && typeof entry.handler !== 'function') {
    throw new TypeError('Action handler is required')
  }
  const key = entry.doctype ? `${entry.doctype}:${entry.name}` : entry.name
  if (stores[kind].has(key)) throw new Error(`Duplicate ${kind} extension: ${key}`)
  if (kind === 'routes' && [...stores.routes.values()].some((route) => route.path === entry.path)) {
    throw new Error(`Duplicate route path: ${entry.path}`)
  }
  const value = Object.freeze({ ...entry })
  stores[kind].set(key, value)
  return () => stores[kind].get(key) === value && stores[kind].delete(key)
}

export function entries(kind) {
  return [...stores[kind].values()]
}
