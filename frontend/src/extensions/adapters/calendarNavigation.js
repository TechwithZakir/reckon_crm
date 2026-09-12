import { getCurrentInstance } from 'vue'

export function calendarUrl() {
  const router = getCurrentInstance()?.appContext.config.globalProperties.$router
  return router?.hasRoute('Calendar') ? router.resolve({ name: 'Calendar' }).href : '/app/event/view/calendar'
}
