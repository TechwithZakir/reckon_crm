import path from 'node:path'
import { transformCRM } from './transform.js'
import { targetFiles } from './compatibility.js'

export function reckonAdapterPlugin(crmFrontend) {
  return {
    name: 'reckon-crm-source-adapter',
    enforce: 'pre',
    transform(source, id) {
      // Vue subrequests contain already-compiled code; only transform the original SFC.
      if (id.includes('?')) return null
      const filename = path.relative(crmFrontend, id).split(path.sep).join('/')
      if (!targetFiles.includes(filename)) return null
      return { code: transformCRM(source, filename), map: null }
    },
  }
}
