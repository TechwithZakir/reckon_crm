import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { createHash } from 'node:crypto'
import { crmRoot } from './paths.mjs'
import { targetFiles } from '../frontend/src/extensions/adapters/compatibility.js'
import { transformCRM } from '../frontend/src/extensions/adapters/transform.js'

export function checkCompatibility(root = crmRoot()) {
  const hashes = {}
  for (const filename of targetFiles) {
    const fullPath = path.join(root, 'frontend', filename)
    if (!fs.existsSync(fullPath)) throw new Error(`CRM source is missing: ${fullPath}`)
    const source = fs.readFileSync(fullPath, 'utf8')
    transformCRM(source, filename)
    hashes[filename] = createHash('sha256').update(source).digest('hex')
  }
  return { schema: 1, source: root, files: hashes }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    console.log(JSON.stringify(checkCompatibility(), null, 2))
  } catch (error) {
    console.error(error.message)
    process.exitCode = 1
  }
}
