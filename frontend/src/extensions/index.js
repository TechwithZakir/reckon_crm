import { registerCRMTab } from './registry/tabs.js'
import { registerCRMRoute } from './registry/routes.js'
import { registerCRMSidebarItem } from './registry/sidebar.js'
import FieldVisits from '../pages/FieldVisits.vue'
import VisitsTab from '../tabs/VisitsTab.vue'

let registered = false
export function registerExtensions() {
  if (registered) return
  registerCRMRoute({ name: 'Reckon Field Visits', path: '/visits', component: FieldVisits })
  registerCRMSidebarItem({
    name: 'Reckon Field Visits', section: 'FIELD SALES', label: 'Field Visits',
    routeName: 'Reckon Field Visits',
  })
  for (const doctype of ['CRM Lead', 'CRM Deal']) {
    registerCRMTab({ doctype, name: 'Visits', label: 'Visits', component: VisitsTab })
  }
  registered = true
}

export { registerCRMTab } from './registry/tabs.js'
export { registerCRMRoute } from './registry/routes.js'
export { registerCRMSidebarItem } from './registry/sidebar.js'
export { registerCRMAction } from './registry/actions.js'
