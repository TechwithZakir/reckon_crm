export const runtimeImport = '@reckon/extensions/adapters/runtime.js'

export function replaceOnce(source, needle, replacement, filename) {
  const count = source.split(needle).length - 1
  if (count !== 1) {
    throw new Error(`Unsupported CRM source: ${filename}; expected one ${JSON.stringify(needle)}, found ${count}. Update the Reckon adapter before building.`)
  }
  return source.replace(needle, replacement)
}

// Upstream CRM filters form tabs with `return tabOptions.filter(` in older
// releases and with `return mergeFormTabs(tabOptions, ...)` on develop (Frappe 16).
const tabReturnAnchors = [
  'return tabOptions.filter(',
  'return mergeFormTabs(tabOptions, ',
]

export function extendTabOptions(source, doctype, surface, filename) {
  source = replaceOnce(source, '<script setup>',
    `<script setup>\nimport { reckonTabs } from '${runtimeImport}'`, filename)
  const anchor = tabReturnAnchors.find((needle) => source.split(needle).length === 2)
  if (!anchor) {
    throw new Error(`Unsupported CRM source: ${filename}; no known tab return anchor. Update the Reckon adapter before building.`)
  }
  return replaceOnce(source, anchor,
    `tabOptions.push(...reckonTabs('${doctype}', '${surface}'))\n  ${anchor}`, filename)
}

export const targetFiles = Object.freeze([
  'src/main.js',
  'src/router.js',
  'src/components/Layouts/AppSidebar.vue',
  'src/pages/Lead.vue', 'src/pages/Deal.vue',
  'src/pages/MobileLead.vue', 'src/pages/MobileDeal.vue',
])
