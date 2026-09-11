import { replaceOnce, runtimeImport, targetFiles } from './compatibility.js'
import { extendDesktop } from './crmDesktopAdapter.js'
import { extendMobile } from './crmMobileAdapter.js'

export function transformCRM(source, filename) {
  if (!targetFiles.includes(filename)) return source
  source = source.replaceAll('\r\n', '\n')
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
