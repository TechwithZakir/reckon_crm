<template>
  <div class="rv-workspace">
    <div class="rv-heading"><h2>Visits</h2><div class="rv-actions"><button v-if="context.can_manage_settings" @click="settingsOpen = !settingsOpen">Visit settings</button><button v-if="context.can_create" class="rv-primary" @click="scheduling = true" :disabled="scheduling">Schedule visit</button></div></div>
    <VisitSettings v-if="settingsOpen" @close="settingsOpen = false" @saved="load" />
    <VisitSchedule v-if="scheduling" :doctype="doctype" :docname="docname" :context="context" @saved="scheduled" @cancel="scheduling = false" />
    <div v-if="selected" ref="detailPanel" tabindex="-1"><VisitDetail :key="selected.name" :visit="selected" :user="context.user" :settings="context.settings" @close="closeDetail" @changed="changed" /></div>
    <p v-if="opening" role="status">Opening visit…</p>
    <div class="rv-actions rv-filters"><label>Status<select v-model="status" @change="load"><option value="">All statuses</option><option>Planned</option><option>Started</option><option>Completed</option><option>Cancelled</option><option>Missed</option></select></label><button :disabled="loading" @click="load">Refresh</button></div>
    <p v-if="error" class="rv-error" role="alert">{{ error }}</p>
    <p v-if="loading" role="status">Loading visits…</p>
    <p v-else-if="!visits.length && !error">No visits found. Schedule your first visit.</p>
    <div v-else class="rv-list">
      <button v-for="visit in visits" :key="visit.name" class="rv-row" @click="open(visit.name)">
        <span><strong>{{ visit.reference_name }}</strong><span>{{ visit.visit_purpose }}</span></span>
        <span>{{ visit.planned_date }} {{ visit.planned_start_time || '' }}</span>
        <span>{{ visit.status }}</span><span>{{ visit.assigned_to }}</span>
        <span class="rv-open-action">{{ visit.assigned_to === context.user && visit.status === 'Planned' ? 'Open visit · Check in' : visit.assigned_to === context.user && visit.status === 'Started' ? 'Open visit · Check out' : 'Open visit · View details' }} →</span>
      </button>
    </div>
    <p class="rv-footnote">Showing the latest 100 accessible visits. Times use your site's timezone. Completed visits are read-only.</p>
  </div>
</template>

<script setup>
import { nextTick, ref, watch } from 'vue'
import VisitSchedule from './VisitSchedule.vue'
import VisitDetail from './VisitDetail.vue'
import VisitSettings from './VisitSettings.vue'
import { api } from '../services/api.js'
import './visits.css'
const props = defineProps({ doctype: String, docname: String })
const visits = ref([]), context = ref({}), selected = ref(null), scheduling = ref(false), status = ref(''), error = ref(''), loading = ref(false)
let generation = 0
let detailGeneration = 0
const detailPanel = ref(null), opening = ref(false)
const settingsOpen = ref(false)
function closeDetail() { detailGeneration++; selected.value = null; opening.value = false }
async function load() {
  const current = ++generation
  loading.value = true; error.value = ''
  try {
    const filters = props.docname ? { reference_doctype: props.doctype, reference_name: props.docname } : {}
    if (status.value) filters.status = status.value
    const [rows, settings] = await Promise.all([api('visits.list_visits', filters, 'GET'), api('visits.context', {}, 'GET')])
    if (current === generation) { visits.value = rows; context.value = settings }
  } catch (e) { if (current === generation) error.value = e.message }
  finally { if (current === generation) loading.value = false }
}
async function open(name) {
  const current = ++detailGeneration
  opening.value = true; error.value = ''
  try {
    const visit = await api('visits.get_visit', { name }, 'GET')
    if (current !== detailGeneration) return
    selected.value = visit; scheduling.value = false
    await nextTick()
    if (current !== detailGeneration) return
    detailPanel.value?.focus({ preventScroll: true })
    detailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  } catch (e) { if (current === detailGeneration) error.value = e.message }
  finally { if (current === detailGeneration) opening.value = false }
}
async function scheduled(visit) { scheduling.value = false; selected.value = visit; await load() }
async function changed(visit) { selected.value = visit; await load() }
watch(() => [props.doctype, props.docname], () => { closeDetail(); scheduling.value = false; load() }, { immediate: true })
</script>
