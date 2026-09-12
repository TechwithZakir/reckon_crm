<template>
  <section class="rv-card" aria-labelledby="visit-title">
    <div class="rv-heading"><h2 id="visit-title">Visit · {{ visit.reference_name }}</h2><button @click="$emit('close')">Close details</button></div>
    <p>{{ visit.planned_date }} {{ visit.planned_start_time || '' }} · {{ visit.status }} · {{ visit.assigned_to }}</p>
    <p class="rv-preserve">{{ visit.visit_purpose }}</p>
    <dl class="rv-grid">
      <div><dt>Check-in verification</dt><dd>{{ visit.geo_status }}</dd></div>
      <div><dt>Distance at check-in</dt><dd>{{ visit.checkin_time && visit.customer_location && visit.geo_status !== 'Location Unavailable' ? `${Math.round(visit.distance_from_customer)}m` : 'Not verified' }}</dd></div>
      <div v-if="visit.checkin_time"><dt>Checked in</dt><dd>{{ visit.checkin_time }} · {{ visit.checkin_by }}</dd></div>
      <div v-if="visit.checkout_time"><dt>Checked out</dt><dd>{{ visit.checkout_time }} · {{ visit.checkout_by }}</dd></div>
      <div v-if="visit.checkout_time"><dt>Duration</dt><dd>{{ visit.duration_minutes }} minutes</dd></div>
      <div v-if="visit.checkout_time"><dt>Check-out verification</dt><dd>{{ visit.checkout_geo_status }}</dd></div>
    </dl>
    <div v-if="visit.status === 'Completed'"><h3>{{ visit.outcome }}</h3><p class="rv-preserve">{{ visit.notes }}</p><p v-if="visit.next_followup_date">Next follow-up: {{ visit.next_followup_date }}</p></div>
    <div v-if="['Planned', 'Started'].includes(visit.status) && visit.assigned_to === user">
      <p v-if="preview">Current check: {{ preview.geo_status }} · {{ preview.distance_from_customer == null ? 'Distance unavailable' : `${Math.round(preview.distance_from_customer)}m away` }} · allowed {{ preview.allowed_radius || 'not set' }}m</p>
      <p>Location is requested only when you use a location action. Outside-radius and unavailable samples are saved as unverified; browser GPS cannot prove presence.</p>
      <div v-if="visit.status === 'Planned'" class="rv-actions">
        <button :disabled="busy" @click="previewLocation">Check distance</button>
        <button class="rv-primary" :disabled="busy" @click="start(false)">Check in with location</button>
        <button :disabled="busy" @click="start(true)">Check in without location</button>
      </div>
      <form v-else @submit.prevent="finish(false)">
        <label>Outcome<input v-model="outcome" maxlength="140" required /></label>
        <label>Notes<textarea v-model="notes" rows="4" maxlength="10000" /></label>
        <label>Next follow-up<input v-model="followup" type="date" /></label>
        <div class="rv-actions"><button class="rv-primary" :disabled="busy" type="submit">Complete with location</button>
          <button :disabled="busy || !outcome.trim()" type="button" @click="finish(true)">Complete without location</button></div>
      </form>
    </div>
    <div v-if="['Planned', 'Started'].includes(visit.status)" class="rv-actions">
      <label>Attach file<input type="file" :disabled="busy" @change="upload($event, 'attachment')" /></label>
      <label>Add photo<input type="file" accept="image/*" :disabled="busy" @change="upload($event, 'photo')" /></label>
      <button v-if="visit.status === 'Planned'" :disabled="busy" @click="cancelVisit">Cancel visit</button>
    </div>
    <div class="rv-actions"><a v-if="visit.attachment" :href="visit.attachment" target="_blank" rel="noopener">View attachment</a><a v-if="visit.photo" :href="visit.photo" target="_blank" rel="noopener">View photo</a></div>
    <p v-if="busy" role="status">Processing…</p><p v-if="error" role="alert" class="rv-error">{{ error }}</p>
  </section>
</template>

<script setup>
import { ref } from 'vue'
import { api, uploadVisitFile } from '../services/api.js'
import { currentPosition } from '../services/geo.js'
const props = defineProps({ visit: { type: Object, required: true }, user: String })
const emit = defineEmits(['changed', 'close'])
const busy = ref(false), error = ref(''), preview = ref(null), outcome = ref(''), notes = ref(''), followup = ref('')
async function run(action) { busy.value = true; error.value = ''; try { await action() } catch (e) { error.value = e.message } finally { busy.value = false } }
async function previewLocation() { await run(async () => { preview.value = await api('geo.preview', { name: props.visit.name, ...await currentPosition() }) }) }
async function start(withoutLocation) { await run(async () => emit('changed', await api('visits.check_in', { name: props.visit.name, ...(withoutLocation ? {} : await currentPosition()) }))) }
async function finish(withoutLocation) { await run(async () => emit('changed', await api('visits.check_out', { name: props.visit.name, outcome: outcome.value, notes: notes.value,
  next_followup_date: followup.value, ...(withoutLocation ? {} : await currentPosition()) }))) }
async function cancelVisit() { await run(async () => emit('changed', await api('visits.cancel', { name: props.visit.name }))) }
async function upload(event, field) {
  const file = event.target.files?.[0]
  if (file) await run(async () => emit('changed', await uploadVisitFile(props.visit.name, field, file)))
  event.target.value = ''
}
</script>
