import fs from 'node:fs'
import path from 'node:path'
import { randomUUID } from 'node:crypto'
import { appRoot, crmRoot } from './paths.mjs'
import { checkCompatibility } from './check-compatibility.mjs'
import { createBuildConfig } from '../frontend/src/extensions/adapters/buildConfig.js'
import { hostPackageLoader } from '../frontend/src/extensions/adapters/hostPackages.js'

try {
  const source = crmRoot()
  const report = checkCompatibility(source)
  const crmFrontend = path.join(source, 'frontend')
  const { build } = await hostPackageLoader(crmFrontend)('vite')
  // Retain the active build until all assets and the boot template are ready.
  const buildId = randomUUID()
  const outDir = path.join(appRoot, 'reckon_crm/public/frontend', buildId)
  const base = `/assets/reckon_crm/frontend/${buildId}/`
  const config = await createBuildConfig({ crmFrontend, appRoot, outDir, base })
  await build(config)
  const html = fs.readFileSync(path.join(outDir, 'index.html'), 'utf8')
  if (!html.includes('{% for key in boot %}') || !html.includes('/assets/reckon_crm/frontend/')) {
    throw new Error('Build is missing CRM boot data or Reckon asset paths; template not activated.')
  }
  const templateDir = path.join(appRoot, 'reckon_crm/templates')
  fs.mkdirSync(templateDir, { recursive: true })
  const extensionVersion = JSON.parse(fs.readFileSync(path.join(appRoot, 'package.json'), 'utf8')).version
  const metadata = { schema: report.schema, files: report.files, buildId, extensionVersion }
  fs.writeFileSync(path.join(templateDir, 'reckon_crm.json.tmp'), JSON.stringify(metadata, null, 2))
  fs.writeFileSync(path.join(templateDir, 'reckon_crm.html.tmp'), html)
  fs.renameSync(path.join(templateDir, 'reckon_crm.json.tmp'), path.join(templateDir, 'reckon_crm.json'))
  fs.renameSync(path.join(templateDir, 'reckon_crm.html.tmp'), path.join(templateDir, 'reckon_crm.html'))
  console.log('Reckon CRM build complete. Migrate your site and run the live field-visit acceptance checklist.')
} catch (error) {
  console.error(`Reckon CRM build failed: ${error.message}`)
  console.error('Install CRM frontend dependencies and set RECKON_CRM_SOURCE if apps/crm is not adjacent.')
  process.exitCode = 1
}
