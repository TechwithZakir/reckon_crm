import assert from 'node:assert/strict'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'
import test from 'node:test'
import { parse, compileScript, compileTemplate } from '@vue/compiler-sfc'
import { crmRoot } from '../../scripts/paths.mjs'
import { targetFiles } from '../../frontend/src/extensions/adapters/compatibility.js'
import { transformCRM } from '../../frontend/src/extensions/adapters/transform.js'

const root = crmRoot()
const refs = process.env.RECKON_TEST_REFS?.split(',') || ['WORKTREE']

for (const ref of refs) {
  test(`compile actual CRM adapter targets: ${ref}`, () => {
    for (const filename of targetFiles) {
      const source = ref === 'WORKTREE'
        ? fs.readFileSync(path.join(root, 'frontend', filename), 'utf8')
        : execFileSync('git', ['-C', root, 'show', `${ref}:frontend/${filename}`], { encoding: 'utf8' })
      const transformed = transformCRM(source, filename)
      assert.notEqual(transformed, source)
      if (filename.endsWith('.vue')) {
        const { descriptor, errors } = parse(transformed, { filename })
        assert.deepEqual(errors, [])
        const script = compileScript(descriptor, { id: filename })
        const result = compileTemplate({ source: descriptor.template.content, filename, id: filename,
          compilerOptions: { bindingMetadata: script.bindings } })
        assert.deepEqual(result.errors, [])
      }
    }
  })
}
