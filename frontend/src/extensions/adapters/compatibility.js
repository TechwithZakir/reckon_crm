export const runtimeImport = '@reckon/extensions/adapters/runtime.js'

export function replaceOnce(source, needle, replacement, filename) {
  const count = source.split(needle).length - 1
  if (count !== 1) {
    throw new Error(`Unsupported CRM source: ${filename}; expected one ${JSON.stringify(needle)}, found ${count}. Update the Reckon adapter before building.`)
  }
  return source.replace(needle, replacement)
}

export function extendTabOptions(source, doctype, surface, filename) {
  source = replaceOnce(source, '<script setup>',
    `<script setup>\nimport { reckonTabs } from '${runtimeImport}'`, filename)
  return replaceOnce(source, 'return tabOptions.filter(',
    `tabOptions.push(...reckonTabs('${doctype}', '${surface}'))\n  return tabOptions.filter(`, filename)
}

export const targetFiles = Object.freeze([
  'src/router.js',
  'src/components/Layouts/AppSidebar.vue',
  'src/pages/Lead.vue', 'src/pages/Deal.vue',
  'src/pages/MobileLead.vue', 'src/pages/MobileDeal.vue',
])
