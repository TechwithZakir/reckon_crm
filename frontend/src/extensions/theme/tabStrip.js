/*
 * Keeps a tab strip's horizontal scroll position when the strip is re-created.
 *
 * Choosing a tab in Frappe CRM re-creates the whole tab strip element, and the new
 * element starts at scroll 0, so a long strip jumps back to its first tab. This
 * remembers the position while the user scrolls, and restores it on each new strip
 * once it has laid out. Plain DOM, no framework or CRM imports.
 */
export function keepTabStripPosition(root = document.body) {
  let saved = 0
  let current = null

  const onScroll = (event) => {
    saved = event.currentTarget.scrollLeft
  }

  // The new strip may not be laid out yet, so retry for about half a second.
  const restore = (el, frames = 30) => {
    requestAnimationFrame(() => {
      if (!el.isConnected || frames <= 0) return
      if (el.scrollWidth > el.clientWidth && el.scrollLeft !== saved) el.scrollLeft = saved
      restore(el, frames - 1)
    })
  }

  const attach = (el) => {
    if (el === current) return
    current = el
    el.addEventListener('scroll', onScroll, { passive: true })
    restore(el)
  }

  const scan = () => {
    const el = document.querySelector('[role="tablist"]')
    if (el) attach(el)
  }

  new MutationObserver(scan).observe(root, { childList: true, subtree: true })
  scan()
}
