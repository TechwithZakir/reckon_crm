<template>
  <div class="rv-workspace">
    <div class="rv-heading"><h2>Visits</h2><Button v-if="context.can_create" theme="gray" variant="solid" label="Schedule visit" :disabled="scheduling" @click="scheduling = true" /></div>
    <VisitSchedule v-if="scheduling" :doctype="doctype" :docname="docname" :context="context" @saved="scheduled" @cancel="scheduling = false" />
    <div v-if="selected" ref="detailPanel" tabindex="-1"><VisitDetail :key="selected.name" :visit="selected" :user="context.user" :settings="context.settings" @close="closeDetail" @changed="changed" /></div>
    <p v-if="opening" role="status">Opening visit…</p>
    <div class="rv-actions rv-filters"><FormControl v-model="status" type="select" label="Status" :options="statusOptions" class="w-48" @update:model-value="load" /><Button label="Refresh" :loading="loading" @click="load" /></div>
    <p v-if="error" class="rv-error" role="alert">{{ error }}</p><p v-if="loading" role="status">Loading visits…</p><p v-else-if="!visits.length && !error">No visits found. Schedule your first visit.</p>
    <ListView v-else :columns="columns" :rows="visits" :options="{ selectable: false, showTooltip: true }" row-key="name" class="rv-list-view">
      <ListHeader><ListHeaderItem v-for="column in columns" :key="column.key" :item="column" /></ListHeader>
      <ListRows v-slot="{ column, item, row }" :rows="visits"><ListRowItem :item="item" class="cursor-pointer" @click="open(row.name)"><template #default="{ label }"><div v-if="column.key === 'reference_name'" class="min-w-0"><div class="truncate text-sm-medium text-ink-gray-9">{{ label }}</div><div class="truncate text-p-sm text-ink-gray-5">{{ row.visit_purpose }}</div></div><span v-else-if="column.key === 'action'" class="text-p-sm text-ink-gray-7">{{ actionLabel(row) }}</span><span v-else>{{ label }}</span></template></ListRowItem></ListRows>
    </ListView>
    <p class="rv-footnote">Showing the latest 100 accessible visits. Times use your site's timezone. Completed visits are read-only.</p>
  </div>
</template>
<script setup>
import { nextTick, ref, watch } from 'vue'
import { Button, FormControl, ListView, ListHeader, ListHeaderItem, ListRowItem } from 'frappe-ui'
import ListRows from '@/components/ListViews/ListRows.vue'
import VisitSchedule from './VisitSchedule.vue'; import VisitDetail from './VisitDetail.vue'; import { api } from '../services/api.js'; import './visits.css'
const props = defineProps({ doctype: String, docname: String })
const visits = ref([]), context = ref({}), selected = ref(null), scheduling = ref(false), status = ref(''), error = ref(''), loading = ref(false), detailPanel = ref(null), opening = ref(false)
const statusOptions = ['', 'Planned', 'Started', 'Completed', 'Cancelled', 'Missed'].map((value) => ({ label: value || 'All statuses', value }))
const columns = [{ label: 'Visit', key: 'reference_name', width: '30%' }, { label: 'When', key: 'planned_date', width: '20%' }, { label: 'Status', key: 'status', width: '15%' }, { label: 'Assigned to', key: 'assigned_to', width: '20%' }, { label: '', key: 'action', width: '15%' }]
let generation = 0; let detailGeneration = 0
function actionLabel(visit) { return visit.assigned_to === context.value.user && visit.status === 'Planned' ? 'Open · Check in' : visit.assigned_to === context.value.user && visit.status === 'Started' ? 'Open · Check out' : 'View details' }
function closeDetail() { detailGeneration++; selected.value = null; opening.value = false }
async function load() { const current = ++generation; loading.value = true; error.value = ''; try { const filters = props.docname ? { reference_doctype: props.doctype, reference_name: props.docname } : {}; if (status.value) filters.status = status.value; const [rows, settings] = await Promise.all([api('visits.list_visits', filters, 'GET'), api('visits.context', {}, 'GET')]); if (current === generation) { visits.value = rows; context.value = settings } } catch (e) { if (current === generation) error.value = e.message } finally { if (current === generation) loading.value = false } }
async function open(name) { const current = ++detailGeneration; opening.value = true; error.value = ''; try { const visit = await api('visits.get_visit', { name }, 'GET'); if (current !== detailGeneration) return; selected.value = visit; scheduling.value = false; await nextTick(); if (current !== detailGeneration) return; detailPanel.value?.focus({ preventScroll: true }); detailPanel.value?.scrollIntoView({ behavior: 'smooth', block: 'start' }) } catch (e) { if (current === detailGeneration) error.value = e.message } finally { if (current === detailGeneration) opening.value = false } }
async function scheduled(visit) { scheduling.value = false; selected.value = visit; await load() }; async function changed(visit) { selected.value = visit; await load() }
watch(() => [props.doctype, props.docname], () => { closeDetail(); scheduling.value = false; load() }, { immediate: true })
</script>
