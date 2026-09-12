<template>
  <section class="rv-card" aria-labelledby="schedule-title">
    <h2 id="schedule-title">Schedule visit</h2>
    <form class="space-y-4" @submit.prevent="submit">
      <div class="rv-grid">
        <FormControl v-model="form.reference_doctype" type="select" label="CRM record type" :disabled="!!doctype" :options="doctypeOptions" @update:model-value="changeType" />
        <FormControl v-if="docname" :model-value="docname" label="CRM record" disabled />
        <template v-else>
          <FormControl v-model="search" label="Find record by ID" placeholder="Search record ID" />
          <div class="rv-field rv-button-field"><Button label="Search records" :loading="busy" @click="loadReferences" /></div>
          <FormControl v-model="form.reference_name" type="select" label="CRM record" required :options="recordOptions" @update:model-value="loadLocations" />
        </template>
        <FormControl v-model="form.visit_type" type="select" label="Visit type" :options="visitTypeOptions" />
        <FormControl v-model="form.planned_date" type="date" label="Date" required />
        <FormControl v-model="form.planned_start_time" type="time" label="Start time" />
        <FormControl v-model="form.planned_end_time" type="time" label="End time" />
        <FormControl v-model="form.customer_location" type="select" label="Customer location" :options="locationOptions" />
      </div>
      <AssigneeSelect v-if="context.can_assign" v-model="assignedUsers" :doctype="form.reference_doctype" :docname="form.reference_name" />
      <LocationMap v-if="selectedLocation" :latitude="selectedLocation.latitude" :longitude="selectedLocation.longitude" />
      <FormControl v-model="form.visit_purpose" type="textarea" label="Purpose" required maxlength="2000" :rows="2" />
      <p class="rv-footnote">Calendar sync: {{ context.settings?.sync_calendar ? 'On' : 'Off' }} · Task sync: {{ context.settings?.sync_tasks ? 'On' : 'Off' }}. Date-only calendar events are all-day; start-only events reserve one hour.</p>
      <p v-if="error" class="rv-error" role="alert">{{ error }}</p>
      <div class="rv-actions"><Button type="submit" theme="gray" variant="solid" :loading="busy" label="Schedule visit" /><Button label="Cancel" :disabled="busy" @click="$emit('cancel')" /><Button v-if="form.reference_name" :label="showLocation ? 'Hide location form' : 'Add customer location'" :disabled="busy" @click="showLocation = !showLocation" /></div>
    </form>
    <form v-if="showLocation" class="rv-location space-y-4" @submit.prevent="saveLocation">
      <h3>New customer location</h3><p>Saving a location requires write access to the linked CRM record.</p>
      <div class="rv-grid">
        <FormControl v-model="location.location_name" label="Location name" required maxlength="140" />
        <FormControl v-model="location.latitude" type="number" label="Latitude" step="any" min="-90" max="90" required />
        <FormControl v-model="location.longitude" type="number" label="Longitude" step="any" min="-180" max="180" required />
        <FormControl v-model="location.geofence_radius" type="number" label="Allowed radius (metres)" min="1" max="10000" required />
      </div>
      <FormControl v-model="location.address" type="textarea" label="Address" :rows="2" />
      <LocationMap :latitude="location.latitude" :longitude="location.longitude" :radius="location.geofence_radius" editable @pick="pickLocation" />
      <div class="rv-actions"><Button type="submit" :loading="busy" label="Save location" /></div>
    </form>
  </section>
</template>
<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Button, FormControl } from 'frappe-ui'
import LocationMap from './LocationMap.vue'
import AssigneeSelect from './AssigneeSelect.vue'
import { api } from '../services/api.js'
const props = defineProps({ doctype: String, docname: String, context: { type: Object, required: true } })
const emit = defineEmits(['saved', 'cancel'])
const today = new Date(); const localDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const form = reactive({ reference_doctype: props.doctype || 'CRM Lead', reference_name: props.docname || '', visit_type: 'Customer Visit', visit_purpose: '', planned_date: localDate, planned_start_time: '', planned_end_time: '', customer_location: '' })
const assignedUsers = ref([props.context.user]); const records = ref([]), locations = ref([]), search = ref(''), error = ref(''), busy = ref(false), showLocation = ref(false)
const location = reactive({ location_name: '', latitude: '', longitude: '', geofence_radius: 100, address: '' })
const doctypeOptions = ['CRM Lead', 'CRM Deal', 'CRM Organization'].map((value) => ({ label: value, value }))
const visitTypeOptions = ['Customer Visit', 'Demo', 'Follow-up', 'Other'].map((value) => ({ label: value, value }))
const recordOptions = computed(() => [{ label: 'Select a record', value: '' }, ...records.value.map((record) => ({ label: `${record.label} (${record.name})`, value: record.name }))])
const locationOptions = computed(() => [{ label: 'No location — check-in will be unverified', value: '' }, ...locations.value.map((item) => ({ label: `${item.location_name} · ${item.geofence_radius}m`, value: item.name }))])
const selectedLocation = computed(() => locations.value.find((item) => item.name === form.customer_location))
async function run(action) { busy.value = true; error.value = ''; try { await action() } catch (e) { error.value = e.message } finally { busy.value = false } }
async function loadReferences() { await run(async () => { records.value = await api('visits.references', { doctype: form.reference_doctype, search: search.value }, 'GET') }) }
async function changeType() { form.reference_name = ''; form.customer_location = ''; locations.value = []; await loadReferences() }
async function loadLocations() { form.customer_location = ''; locations.value = []; if (!form.reference_name) return; await run(async () => { locations.value = await api('geo.locations', { reference_doctype: form.reference_doctype, reference_name: form.reference_name }, 'GET') }) }
async function submit() { await run(async () => { const visits = await api('visits.schedule_many', { data: form, users: assignedUsers.value }); emit('saved', visits[0]) }) }
function pickLocation(position) { location.latitude = position.latitude; location.longitude = position.longitude }
async function saveLocation() { await run(async () => { const saved = await api('geo.create_location', { data: { ...location, reference_doctype: form.reference_doctype, reference_name: form.reference_name } }); locations.value.push(saved); form.customer_location = saved.name; showLocation.value = false }) }
onMounted(() => props.docname ? loadLocations() : loadReferences())
</script>
