<template>
  <section class="rv-card" aria-label="Visit settings">
    <div class="rv-heading"><h2>Visit settings</h2><button @click="$emit('close')">Close settings</button></div>
    <p>Choose which records visits create and update. Changes apply to future saves and check-ins; existing records are retained when sync is disabled.</p>
    <form v-if="loaded" @submit.prevent="save">
      <label class="rv-check"><input type="checkbox" v-model="values.sync_calendar" />Sync visits to Calendar</label>
      <label class="rv-check"><input type="checkbox" v-model="values.sync_tasks" />Create and sync assigned CRM Tasks</label>
      <label class="rv-check"><input type="checkbox" v-model="values.sync_employee_checkin" :disabled="!hrms" />Sync visit check-in/out to Employee Checkin (HRMS)</label>
      <p v-if="!hrms">Install HRMS to enable employee logs.</p>
      <label v-if="values.sync_employee_checkin" class="rv-check"><input type="checkbox" v-model="values.skip_auto_attendance" />Skip auto attendance for visit logs</label>
      <p v-if="values.sync_employee_checkin">Each visitor needs one active Employee linked to their user and permission to create Employee Checkin. HRMS shift and geofence rules apply. Clearing Skip auto attendance lets these visit logs affect attendance calculations.</p>
      <button type="submit" class="rv-primary" :disabled="busy">{{ busy ? 'Saving…' : 'Save settings' }}</button>
    </form>
    <p v-if="!loaded && !error" role="status">Loading settings…</p>
    <p v-if="error" class="rv-error" role="alert">{{ error }}</p>
    <p v-if="saved" role="status">Settings saved.</p>
  </section>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../services/api.js'
const emit = defineEmits(['close', 'saved'])
const values = reactive({ sync_calendar: true, sync_tasks: false, sync_employee_checkin: false, skip_auto_attendance: true })
const hrms = ref(false), loaded = ref(false), busy = ref(false), error = ref(''), saved = ref(false)
onMounted(async () => {
  try { const result = await api('settings.read', {}, 'GET'); for (const key in values) values[key] = !!result[key]; hrms.value = result.hrms_installed; loaded.value = true }
  catch (e) { error.value = e.message }
})
async function save() {
  busy.value = true; error.value = ''; saved.value = false
  try { await api('settings.save', { data: Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Number(value)])) }); saved.value = true; emit('saved') }
  catch (e) { error.value = e.message } finally { busy.value = false }
}
</script>
