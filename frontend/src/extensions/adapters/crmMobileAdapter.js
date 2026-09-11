import { extendTabOptions, replaceOnce } from './compatibility.js'

export function extendMobile(source, doctype, filename) {
  source = extendTabOptions(source, doctype, 'mobile', filename)
  const id = doctype === 'CRM Lead' ? 'leadId' : 'dealId'
  return replaceOnce(source, '<Activities\n          v-else', `<component
          v-else-if="tab.reckonComponent"
          :is="tab.reckonComponent"
          doctype="${doctype}"
          :docname="${id}"
        />
        <Activities
          v-else`, filename)
}
