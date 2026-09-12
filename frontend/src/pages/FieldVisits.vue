<template>
  <LayoutHeader>
    <template #left-header><h1 class="reckon-title">Field Visits</h1></template>
    <template #right-header><RouterLink v-if="canManageSettings" class="reckon-settings-link" :to="{name:'Reckon Visit Settings'}">Visit settings</RouterLink></template>
  </LayoutHeader>
  <main class="reckon-visits"><VisitWorkspace /></main>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import LayoutHeader from '@/components/LayoutHeader.vue'
import VisitWorkspace from '../components/VisitWorkspace.vue'
import { api } from '../services/api.js'
const canManageSettings = ref(false)
onMounted(async () => {
  try { canManageSettings.value = !!(await api('visits.context', {}, 'GET')).can_manage_settings } catch { /* Workspace retains its own errors. */ }
})
</script>

<style scoped>
.reckon-title { font-size: 16px; font-weight: 600; }
.reckon-visits { display: flex; flex: 1; min-width: 0; overflow: auto; }
.reckon-settings-link { color:var(--ink-gray-7,#525252); font-size:14px; text-decoration:none; }
</style>
