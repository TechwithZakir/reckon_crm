import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'
import { pathToFileURL } from 'node:url'

// Resolve import-only package exports from the host, without generating a loader
// inside apps/crm or taking a second copy of Vue from Reckon's dependencies.
export function hostPackageLoader(frontend) {
  const resolver = createRequire(path.join(frontend, 'package.json'))
  return async (specifier) => {
    const parts = specifier.split('/')
    const count = specifier.startsWith('@') ? 2 : 1
    const packageName = parts.slice(0, count).join('/')
    const subpath = parts.length > count ? './' + parts.slice(count).join('/') : '.'
    const directory = resolver.resolve.paths(packageName)
      .map((base) => path.join(base, packageName))
      .find((base) => fs.existsSync(path.join(base, 'package.json')))
    if (!directory) throw new Error(`Install CRM frontend dependency: ${packageName}`)
    const metadata = JSON.parse(fs.readFileSync(path.join(directory, 'package.json'), 'utf8'))
    let entry = metadata.exports
    if (entry && Object.keys(entry).some((key) => key.startsWith('.'))) entry = entry[subpath]
    while (entry && typeof entry === 'object') entry = entry.import || entry.node || entry.default
    if (!entry && !metadata.exports) entry = subpath === '.' ? metadata.module || metadata.main : subpath
    if (typeof entry !== 'string') throw new Error(`Unsupported host package export: ${specifier}`)
    return import(pathToFileURL(path.join(directory, entry)).href)
  }
}
