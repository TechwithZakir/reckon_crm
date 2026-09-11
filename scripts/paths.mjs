import path from 'node:path'
import { fileURLToPath } from 'node:url'

export const appRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
export function crmRoot() {
  return path.resolve(process.env.RECKON_CRM_SOURCE || path.join(appRoot, '../crm'))
}
