import { entries, register } from './store.js'
export const registerCRMRoute = (entry) => register('routes', entry)
export const getCRMRoutes = () => entries('routes')
