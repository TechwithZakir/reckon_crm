<template>
  <div class="copilot">
    <div v-if="loading" class="muted">Reading the lead…</div>
    <div v-else-if="error" class="muted">{{ error }}</div>
    <div v-else-if="!data.linked" class="muted">
      {{ data.reason || 'No Sales Agent record for this lead yet.' }}
    </div>
    <template v-else>
      <p>{{ data.summary }}</p>
      <p><b>Next step:</b> {{ data.next_step }}</p>
      <ul v-if="data.risks && data.risks.length">
        <li v-for="risk in data.risks" :key="risk">{{ risk }}</li>
      </ul>
      <div class="muted small">
        {{ data.source === 'ai' ? 'AI summary, read-only' : 'Summary from CRM facts, read-only' }}
      </div>
      <button class="btn" @click="load">Refresh</button>
    </template>
  </div>
</template>

<script setup>
import { onMounted, ref, watch } from 'vue'
import { api } from '../services/api.js'

const props = defineProps({
  doctype: { type: String, required: true },
  docname: { type: String, required: true },
})

const data = ref({})
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    data.value = await api('copilot.summary', { doctype: props.doctype, docname: props.docname })
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => props.docname, load)
</script>
