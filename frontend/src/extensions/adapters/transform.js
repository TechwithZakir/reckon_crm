import { replaceOnce, runtimeImport, targetFiles } from './compatibility.js'
import { extendDesktop } from './crmDesktopAdapter.js'
import { extendMobile } from './crmMobileAdapter.js'

export function transformCRM(source, filename) {
  if (!targetFiles.includes(filename)) return source
  source = source.replaceAll('\r\n', '\n')
  if (filename === 'src/main.js') {
    // Load the Aura skin after frappe-ui's own CSS so its tokens win.
    // The Aura skin loads after frappe-ui's CSS so its tokens win; the tools
    // dock mounts once the page is up, driven by the Aura Theme Settings.
    source = replaceOnce(source, "import './index.css'",
      "import './index.css'\nimport '@reckon/extensions/theme/aura-desk-ui.css'\nimport '@reckon/extensions/theme/aura-crm.css'\nimport { mountAuraDock } from '@reckon/extensions/theme/auraDock.js'\nmountAuraDock()", filename)
    return source
  }
  if (filename === 'src/router.js') {
    if (/path:\s*['"]\/visits['"]/.test(source)) {
      throw new Error('CRM already defines /visits; resolve the route collision in the adapter.')
    }
    return `import { reckonRoutes } from '${runtimeImport}'\n` + replaceOnce(
      source, 'const routes = [', 'const routes = [\n  ...reckonRoutes(),', filename,
    )
  }
  if (filename === 'src/components/Layouts/AppSidebar.vue') {
    source = replaceOnce(source, '<script setup>',
      `<script setup>\nimport { reckonSidebarSections } from '${runtimeImport}'`, filename)
    return replaceOnce(source, 'return _views', 'return [..._views, ...reckonSidebarSections()]', filename)
  }
  const doctype = filename.includes('Lead') ? 'CRM Lead' : 'CRM Deal'
  return filename.includes('/Mobile')
    ? extendMobile(source, doctype, filename)
    : extendDesktop(source, doctype, filename)
}
