import { markRaw } from 'vue'
import { registerExtensions } from '../index.js'
import { getCRMTabs } from '../registry/tabs.js'
import { getCRMRoutes } from '../registry/routes.js'
import { getCRMSidebarItems } from '../registry/sidebar.js'
import VisitIcon from '../../components/VisitIcon.vue'

registerExtensions()

export function reckonTabs(doctype, surface) {
  return getCRMTabs(doctype, surface).map((tab) => ({
    name: tab.name, label: tab.label, icon: markRaw(VisitIcon),
    reckonComponent: markRaw(tab.component),
  }))
}

export function reckonRoutes() {
  return getCRMRoutes().map(({ name, path, component }) => ({ name, path, component }))
}

export function reckonSidebarSections() {
  const sections = new Map()
  for (const item of getCRMSidebarItems()) {
    if (!sections.has(item.section)) {
      sections.set(item.section, { name: item.section, opened: true, views: [] })
    }
    sections.get(item.section).views.push({
      label: item.label, key: item.routeName, to: { name: item.routeName },
      icon: markRaw(VisitIcon),
    })
  }
  return [...sections.values()]
}
