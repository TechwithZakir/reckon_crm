<template>
  <section class="rv-card" aria-label="Visit settings">
    <div class="rv-heading"><h2>Visit settings</h2></div>
    <p>Choose which native records visits create and update. Each option applies independently to future actions.</p>
    <form v-if="loaded" class="rv-settings-form" @submit.prevent="save">
      <Checkbox v-model="values.sync_calendar" label="Sync visits to Calendar" />
      <Checkbox v-model="values.sync_tasks" label="Create and sync assigned CRM Tasks" />
      <Checkbox v-model="values.sync_employee_checkin" :disabled="!hrms" label="Sync visit check-in/out to Employee Checkin (HRMS)" />
      <p v-if="!hrms" class="text-p-sm text-ink-gray-5">Install HRMS to enable employee logs.</p>
      <Checkbox v-if="values.sync_employee_checkin" v-model="values.skip_auto_attendance" label="Skip auto attendance for visit logs" />
      <p v-if="values.sync_employee_checkin" class="text-p-sm text-ink-gray-5">Each visitor needs one active Employee linked to their user and permission to create Employee Checkin. HRMS shift and geofence rules apply.</p>
      <Button type="submit" theme="gray" variant="solid" :loading="busy" label="Save settings" class="w-fit" />
    </form>
    <p v-if="!loaded && !error" role="status">Loading settings…</p><p v-if="error" class="rv-error" role="alert">{{ error }}</p><p v-if="saved" role="status">Settings saved.</p>
  </section>
</template>
<script setup>
import { onMounted, reactive, ref } from 'vue'
import { Button, Checkbox } from 'frappe-ui'
import { api } from '../services/api.js'
const emit = defineEmits(['saved'])
const values = reactive({ sync_calendar: true, sync_tasks: false, sync_employee_checkin: false, skip_auto_attendance: true })
const hrms = ref(false), loaded = ref(false), busy = ref(false), error = ref(''), saved = ref(false)
onMounted(async () => { try { const result = await api('settings.read', {}, 'GET'); for (const key in values) values[key] = !!result[key]; hrms.value = result.hrms_installed; loaded.value = true } catch (e) { error.value = e.message } })
async function save() { busy.value = true; error.value = ''; saved.value = false; try { await api('settings.save', { data: Object.fromEntries(Object.entries(values).map(([key, value]) => [key, Number(value)])) }); saved.value = true; emit('saved') } catch (e) { error.value = e.message } finally { busy.value = false } }
</script>
