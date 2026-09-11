import assert from 'node:assert/strict'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { transformCRM } from '../../frontend/src/extensions/adapters/transform.js'
import { replaceOnce } from '../../frontend/src/extensions/adapters/compatibility.js'

export function compileVue(source, filename) {
  const { descriptor, errors } = parse(source, { filename })
  assert.deepEqual(errors, [])
  const script = compileScript(descriptor, { id: filename })
  const template = compileTemplate({ source: descriptor.template.content, filename, id: filename,
    compilerOptions: { bindingMetadata: script.bindings } })
  assert.deepEqual(template.errors, [])
  return template.code
}

test('incompatible and ambiguous upstream anchors stop the build', () => {
  assert.throws(() => transformCRM('const pages = []', 'src/router.js'), /Unsupported CRM source/)
  assert.throws(() => replaceOnce('abc abc', 'abc', 'x', 'file'), /found 2/)
  assert.equal(transformCRM('unrelated', 'src/other.js'), 'unrelated')
  assert.throws(() => transformCRM("const routes = [{ path: '/visits' }]", 'src/router.js'), /collision/)
})

for (const mobile of [false, true]) {
  for (const entity of ['Lead', 'Deal']) {
    test(`${mobile ? 'mobile' : 'desktop'} ${entity} adds a Visits panel and preserves native Activities`, () => {
      const file = `src/pages/${mobile ? 'Mobile' : ''}${entity}.vue`
      const source = `<template><Tabs><template #tab-panel="{ tab }">
        ${mobile ? '<div v-if="tab.name === \'Details\'">Native details</div>' : ''}
        <Activities\n${mobile ? '          v-else\n' : ''}          :tabs="tabs" />
      </template></Tabs></template>
      <script setup>
      import { computed } from 'vue'
      const tabs = computed(() => {
        let tabOptions = [{ name: 'Activity' }]
        return tabOptions.filter((tab) => true)
      })
      </script>`
      const output = transformCRM(source, file)
      assert.match(output, /reckonComponent/)
      assert.match(output, /<Activities\s+v-else/)
      assert.match(output, new RegExp(`reckonTabs\\('CRM ${entity}', '${mobile ? 'mobile' : 'desktop'}'\\)`))
      compileVue(output, file)
    })
  }
}

test('all Reckon Vue components compile', () => {
  for (const dir of ['components', 'pages', 'tabs']) {
    const root = path.resolve('frontend/src', dir)
    for (const file of fs.readdirSync(root).filter((name) => name.endsWith('.vue'))) {
      const source = fs.readFileSync(path.join(root, file), 'utf8')
      const { descriptor, errors } = parse(source)
      assert.deepEqual(errors, [])
      if (descriptor.scriptSetup) compileVue(source, file)
      else assert.deepEqual(compileTemplate({ source: descriptor.template.content, filename: file, id: file }).errors, [])
    }
  }
})
