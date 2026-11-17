import test from 'node:test'
import assert from 'node:assert/strict'
import fs from 'node:fs'

const theme = new URL('../../frontend/src/extensions/theme/', import.meta.url)
const read = (name) => fs.readFileSync(new URL(name, theme), 'utf8')

test('the CRM Ask panel is the Desk Ask Aura AI panel: same classes, chat API and shortcut', () => {
  const dock = read('auraDock.js')
  for (const marker of ['Ask Aura AI', 'aura-ask-header', 'aura-ask-composer', 'aura-chat-turn', 'aura-ask-voice',
    'Dock to right', 'reckon_aura_theme.api.ask', 'history', 'event.key.toLowerCase() === \'j\'']) {
    assert.ok(dock.includes(marker), marker)
  }
  assert.ok(!dock.includes('about your CRM…'), 'the old one-line command box is gone')
})

test('the tools sit in the CRM sidebar bottom group and float only as a fallback', () => {
  const dock = read('auraDock.js')
  assert.ok(dock.includes("#app div.mt-auto.flex.flex-col.gap-1.pt-2"))
  assert.ok(dock.includes('insertBefore(inSidebar, group.firstChild)'))
  assert.ok(dock.includes('aura-tools--dock'))
})

test('no dock mouse handler cancels the browser default, so text selection and focus work', () => {
  const dock = read('auraDock.js')
  assert.ok(!/addEventListener\('mousedown'[^)]*\) => false/.test(dock))
  // Only the padding of the message box prevents the default (to focus the box); the rest of the panel is left alone.
  const handlers = dock.split("root.addEventListener('mousedown'").slice(1)
  assert.equal(handlers.length, 2)
  assert.ok(!handlers[0].split('})')[0].includes('preventDefault'))
})

test('the CRM stylesheet carries the Desk Ask panel rules', () => {
  const css = read('aura-desk-ui.css')
  for (const selector of ['.aura-chat-turn', '.aura-ask-composer', '.aura-ask-header', '.aura-ask-backdrop.is-docked']) {
    assert.ok(css.includes(selector), selector)
  }
  assert.ok(read('aura-crm.css').includes('.aura-tools--sidebar'))
})
