import { entries, register } from './store.js'
export const registerCRMTab = (entry) => register('tabs', entry)
export const getCRMTabs = (doctype, surface = 'desktop') => entries('tabs').filter(
  (tab) => tab.doctype === doctype && (!tab.surfaces || tab.surfaces.includes(surface)),
)
