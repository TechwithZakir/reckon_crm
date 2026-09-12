<template>
  <section class="rv-card" aria-labelledby="schedule-title">
    <h2 id="schedule-title">Schedule visit</h2>
    <form @submit.prevent="submit">
      <div class="rv-grid">
        <label>CRM record type<select v-model="form.reference_doctype" :disabled="!!doctype" @change="changeType">
          <option>CRM Lead</option><option>CRM Deal</option><option>CRM Organization</option>
        </select></label>
        <label v-if="docname">CRM record<input :value="docname" readonly /></label>
        <template v-else>
          <label>Find record by ID<input v-model="search" placeholder="Search record ID" /></label>
          <button type="button" @click="loadReferences" :disabled="busy">Search records</button>
          <label>CRM record<select v-model="form.reference_name" required @change="loadLocations">
            <option value="">Select a record</option>
            <option v-for="record in records" :key="record.name" :value="record.name">{{ record.label }} ({{ record.name }})</option>
          </select></label>
        </template>
        <label>Visit type<select v-model="form.visit_type"><option>Customer Visit</option><option>Demo</option><option>Follow-up</option><option>Other</option></select></label>
        <label>Date<input v-model="form.planned_date" type="date" required /></label>
        <label>Start time<input v-model="form.planned_start_time" type="time" /></label>
        <label>End time<input v-model="form.planned_end_time" type="time" /></label>
        <label v-if="context.can_assign">Assigned user email<input v-model="form.assigned_to" required /></label>
        <label>Customer location<select v-model="form.customer_location">
          <option value="">No location — check-in will be unverified</option>
          <option v-for="location in locations" :key="location.name" :value="location.name">{{ location.location_name }} · {{ location.geofence_radius }}m</option>
        </select></label>
      </div>
      <label>Purpose<textarea v-model="form.visit_purpose" required maxlength="2000" rows="2" /></label>
      <p v-if="error" class="rv-error" role="alert">{{ error }}</p>
      <div class="rv-actions"><button class="rv-primary" :disabled="busy" type="submit">{{ busy ? 'Saving…' : 'Schedule visit' }}</button>
        <button type="button" @click="$emit('cancel')" :disabled="busy">Cancel</button>
        <button v-if="form.reference_name" type="button" @click="showLocation = !showLocation">{{ showLocation ? 'Hide location form' : 'Add customer location' }}</button>
      </div>
    </form>
    <form v-if="showLocation" class="rv-location" @submit.prevent="saveLocation">
      <h3>New customer location</h3><p>Saving a location requires write access to the linked CRM record.</p>
      <div class="rv-grid">
        <label>Location name<input v-model="location.location_name" required maxlength="140" /></label>
        <label>Latitude<input v-model="location.latitude" type="number" step="any" min="-90" max="90" required /></label>
        <label>Longitude<input v-model="location.longitude" type="number" step="any" min="-180" max="180" required /></label>
        <label>Allowed radius (metres)<input v-model="location.geofence_radius" type="number" min="1" max="10000" required /></label>
      </div>
      <label>Address<textarea v-model="location.address" rows="2" /></label>
      <div class="rv-actions"><button :disabled="busy" type="button" @click="locate">Use current location</button><button :disabled="busy" type="submit">Save location</button></div>
    </form>
  </section>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { api } from '../services/api.js'
import { currentPosition } from '../services/geo.js'
const props = defineProps({ doctype: String, docname: String, context: { type: Object, required: true } })
const emit = defineEmits(['saved', 'cancel'])
const today = new Date()
const localDate = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
const form = reactive({ reference_doctype: props.doctype || 'CRM Lead', reference_name: props.docname || '', visit_type: 'Customer Visit',
  visit_purpose: '', planned_date: localDate, planned_start_time: '', planned_end_time: '', assigned_to: props.context.user, customer_location: '' })
const records = ref([]), locations = ref([]), search = ref(''), error = ref(''), busy = ref(false), showLocation = ref(false)
const location = reactive({ location_name: '', latitude: '', longitude: '', geofence_radius: 100, address: '' })
async function run(action) {
  busy.value = true; error.value = ''
  try { await action() } catch (e) { error.value = e.message } finally { busy.value = false }
}
async function loadReferences() { await run(async () => { records.value = await api('visits.references', { doctype: form.reference_doctype, search: search.value }, 'GET') }) }
async function changeType() { form.reference_name = ''; form.customer_location = ''; locations.value = []; await loadReferences() }
async function loadLocations() {
  form.customer_location = ''; locations.value = []
  if (!form.reference_name) return
  await run(async () => { locations.value = await api('geo.locations', { reference_doctype: form.reference_doctype, reference_name: form.reference_name }, 'GET') })
}
async function submit() { await run(async () => emit('saved', await api('visits.schedule', { data: form }))) }
async function locate() { await run(async () => { const position = await currentPosition(); location.latitude = position.latitude; location.longitude = position.longitude }) }
async function saveLocation() {
  await run(async () => {
    const saved = await api('geo.create_location', { data: { ...location, reference_doctype: form.reference_doctype, reference_name: form.reference_name } })
    locations.value.push(saved); form.customer_location = saved.name; showLocation.value = false
  })
}
onMounted(() => props.docname ? loadLocations() : loadReferences())
</script>
