import { entries, register } from './store.js'
export const registerCRMSidebarItem = (entry) => register('sidebar', entry)
export const getCRMSidebarItems = () => entries('sidebar')
