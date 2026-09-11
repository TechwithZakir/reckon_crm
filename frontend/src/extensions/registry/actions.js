import { entries, register } from './store.js'
export const registerCRMAction = (entry) => register('actions', entry)
export const getCRMActions = (doctype) => entries('actions').filter((entry) => entry.doctype === doctype)
