<template>
  <section class="rv-card" aria-labelledby="visit-title">
    <div class="rv-heading"><h2 id="visit-title">Visit · {{ visit.reference_name }}</h2><Button label="Close details" @click="$emit('close')" /></div>
    <p>{{ visit.planned_date }} {{ visit.planned_start_time || '' }} · {{ visit.status }} · {{ visit.assigned_to }}</p>
    <p class="rv-preserve">{{ visit.visit_purpose }}</p>
    <p v-if="visit.calendar_event">Synced to Calendar · <a :href="calendarHref">Open calendar</a></p>
    <Button v-else-if="settings.sync_calendar && ['Planned', 'Started'].includes(visit.status)" label="Sync to calendar" :loading="busy" @click="syncCalendar" />
    <p v-if="visit.crm_task">Assigned CRM Task: {{ visit.crm_task }}</p>
    <p v-if="visit.employee_checkin">Employee IN log: {{ visit.employee_checkin }}</p>
    <p v-if="visit.employee_checkout">Employee OUT log: {{ visit.employee_checkout }}</p>
    <dl class="rv-grid">
      <div><dt>Check-in verification</dt><dd>{{ visit.geo_status }}</dd></div>
      <div><dt>Distance at check-in</dt><dd>{{ visit.checkin_time && visit.customer_location && visit.geo_status !== 'Location Unavailable' ? `${Math.round(visit.distance_from_customer)}m` : 'Not verified' }}</dd></div>
      <div v-if="visit.checkin_time"><dt>Checked in</dt><dd>{{ visit.checkin_time }} · {{ visit.checkin_by }}</dd></div>
      <div v-if="visit.checkout_time"><dt>Checked out</dt><dd>{{ visit.checkout_time }} · {{ visit.checkout_by }}</dd></div>
      <div v-if="visit.checkout_time"><dt>Duration</dt><dd>{{ visit.duration_minutes }} minutes</dd></div>
      <div v-if="visit.checkout_time"><dt>Check-out verification</dt><dd>{{ visit.checkout_geo_status }}</dd></div>
    </dl>
    <LocationMap v-if="visit.checkin_time && visit.geo_status !== 'Location Unavailable'" title="Check-in location" :latitude="visit.checkin_latitude" :longitude="visit.checkin_longitude" />
    <LocationMap v-if="visit.checkout_time && visit.checkout_geo_status !== 'Location Unavailable'" title="Check-out location" :latitude="visit.checkout_latitude" :longitude="visit.checkout_longitude" />
    <p v-if="['Planned', 'Started'].includes(visit.status) && visit.assigned_to !== user">Only {{ visit.assigned_to }} can check in or check out this visit.</p>
    <div v-if="visit.status === 'Completed'"><h3>{{ visit.outcome }}</h3><p class="rv-preserve">{{ visit.notes }}</p><p v-if="visit.next_followup_date">Next follow-up: {{ visit.next_followup_date }}</p></div>
    <div v-if="['Planned', 'Started'].includes(visit.status) && visit.assigned_to === user">
      <LocationMap title="Current location" :latitude="captured?.latitude" :longitude="captured?.longitude" locate-enabled @located="captured = $event" />
      <p v-if="settings.sync_employee_checkin">Employee IN/OUT sync is enabled. HRMS permissions and shift rules apply to this action.</p>
      <p v-if="preview">Current check: {{ preview.geo_status }} · {{ preview.distance_from_customer == null ? 'Distance unavailable' : `${Math.round(preview.distance_from_customer)}m away` }} · allowed {{ preview.allowed_radius || 'not set' }}m</p>
      <p>Location is requested only when you use a location action. Outside-radius and unavailable samples are saved as unverified; browser GPS cannot prove presence.</p>
      <div v-if="visit.status === 'Planned'" class="rv-actions">
        <Button label="Check distance" :loading="busy" @click="previewLocation" />
        <Button theme="gray" variant="solid" label="Check in with location" :loading="busy" @click="start(false)" />
        <Button label="Check in without location" :disabled="busy" @click="start(true)" />
      </div>
      <form v-else @submit.prevent="finish(false)">
        <FormControl v-model="outcome" label="Outcome" maxlength="140" required />
        <FormControl v-model="notes" type="textarea" label="Notes" :rows="4" maxlength="10000" />
        <FormControl v-model="followup" type="date" label="Next follow-up" />
        <div class="rv-actions"><Button theme="gray" variant="solid" :loading="busy" type="submit" label="Complete with location" />
          <Button label="Complete without location" :disabled="busy || !outcome.trim()" @click="finish(true)" /></div>
      </form>
    </div>
    <div v-if="['Planned', 'Started'].includes(visit.status)" class="rv-actions">
      <label>Attach file<input type="file" :disabled="busy" @change="upload($event, 'attachment')" /></label>
      <label>Add photo<input type="file" accept="image/*" :disabled="busy" @change="upload($event, 'photo')" /></label>
      <Button v-if="visit.status === 'Planned'" label="Cancel visit" :disabled="busy" @click="cancelVisit" />
    </div>
    <div class="rv-actions"><a v-if="visit.attachment" :href="visit.attachment" target="_blank" rel="noopener">View attachment</a><a v-if="visit.photo" :href="visit.photo" target="_blank" rel="noopener">View photo</a></div>
    <p v-if="busy" role="status">Processing…</p><p v-if="error" role="alert" class="rv-error">{{ error }}</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { Button, FormControl } from 'frappe-ui'
import LocationMap from './LocationMap.vue'
import { calendarUrl } from '../extensions/adapters/calendarNavigation.js'
import { api, uploadVisitFile } from '../services/api.js'
import { currentPosition } from '../services/geo.js'
const props = defineProps({ visit: { type: Object, required: true }, user: String, settings: {type:Object,default:()=>({})} })
const emit = defineEmits(['changed', 'close'])
const calendarHref = calendarUrl()
const busy = ref(false), error = ref(''), preview = ref(null), outcome = ref(''), notes = ref(''), followup = ref('')
const captured = ref(null)
async function capture() { captured.value = await currentPosition(); return captured.value }
async function run(action) { busy.value = true; error.value = ''; try { await action() } catch (e) { error.value = e.message } finally { busy.value = false } }
async function previewLocation() { await run(async () => { preview.value = await api('geo.preview', { name: props.visit.name, ...await capture() }) }) }
async function syncCalendar() { await run(async () => emit('changed', await api('visits.sync_calendar', { name: props.visit.name }))) }
async function start(withoutLocation) { await run(async () => emit('changed', await api('visits.check_in', { name: props.visit.name, ...(withoutLocation ? {} : await capture()) }))) }
async function finish(withoutLocation) { await run(async () => emit('changed', await api('visits.check_out', { name: props.visit.name, outcome: outcome.value, notes: notes.value,
  next_followup_date: followup.value, ...(withoutLocation ? {} : await capture()) }))) }
async function cancelVisit() { await run(async () => emit('changed', await api('visits.cancel', { name: props.visit.name }))) }
async function upload(event, field) {
  const file = event.target.files?.[0]
  if (file) await run(async () => emit('changed', await uploadVisitFile(props.visit.name, field, file)))
  event.target.value = ''
}
</script>
