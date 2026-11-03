<template>
  <div class="flex flex-col gap-4 p-4 text-base text-ink-gray-8">
    <div class="flex items-center justify-between gap-2">
      <div class="flex flex-col">
        <span class="text-sm font-semibold text-ink-gray-9">Copilot</span>
        <span class="text-xs text-ink-gray-5">Sales Agent read on this lead</span>
      </div>
      <span
        v-if="data.linked"
        class="rounded-full border border-outline-gray-2 px-2 py-0.5 text-xs text-ink-gray-6"
      >
        {{ data.source === 'ai' ? 'AI' : 'From CRM facts' }}
      </span>
    </div>

    <div v-if="loading" class="text-sm text-ink-gray-5">Reading the lead…</div>

    <div v-else-if="error" class="text-sm text-ink-gray-6">{{ error }}</div>

    <div v-else-if="!data.linked" class="text-sm text-ink-gray-6">
      {{ data.reason || 'No Sales Agent record for this lead yet.' }}
    </div>

    <template v-else>
      <p class="leading-relaxed text-ink-gray-8">{{ data.summary }}</p>

      <div class="rounded-md border border-outline-gray-2 bg-surface-gray-1 p-3">
        <div class="mb-1 text-xs font-medium uppercase tracking-wide text-ink-gray-5">Next step</div>
        <div class="text-sm text-ink-gray-9">{{ data.next_step }}</div>
      </div>

      <div v-if="data.risks && data.risks.length" class="flex flex-col gap-1">
        <div class="text-xs font-medium uppercase tracking-wide text-ink-gray-5">Watch out</div>
        <ul class="flex flex-col gap-1 text-sm text-ink-gray-7">
          <li v-for="risk in data.risks" :key="risk" class="flex gap-2">
            <span aria-hidden="true">•</span>
            <span>{{ risk }}</span>
          </li>
        </ul>
      </div>

      <div class="flex items-center justify-between border-t border-outline-gray-2 pt-3">
        <span class="text-xs text-ink-gray-5">Read-only. Nothing in CRM is changed.</span>
        <button class="text-sm font-medium text-ink-gray-7 hover:text-ink-gray-9" @click="load">
          Refresh
        </button>
      </div>
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
