import { extendTabOptions, replaceOnce } from './compatibility.js'

export function extendDesktop(source, doctype, filename) {
  source = extendTabOptions(source, doctype, 'desktop', filename)
  const id = doctype === 'CRM Lead' ? 'leadId' : 'dealId'
  return replaceOnce(source, '<Activities\n', `<component
          v-if="tabs[tabIndex]?.reckonComponent"
          :is="tabs[tabIndex].reckonComponent"
          doctype="${doctype}"
          :docname="${id}"
        />
        <Activities
          v-else
`, filename)
}
