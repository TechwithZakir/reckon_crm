<template>
  <section class="rv-field rv-assignees" aria-label="Assigned users">
    <MultiSelect
      :model-value="modelValue"
      :options="options"
      :loading="busy"
      :disabled="!docname"
      label="Assigned users"
      placeholder="Select users"
      empty-text="No eligible users found"
      description="A separate visit is created for each selected user (maximum 25)."
      class="w-full"
      @update:model-value="emit('update:modelValue', $event)"
      @update:open="opened"
    >
      <template #summary="{ selectedOptions, summary }">
        {{ selectedOptions.length ? selectedOptions.map((user) => user.label).join(', ') : summary }}
      </template>
      <template #item-label="{ item }">
        <div class="min-w-0"><div class="truncate">{{ item.label }}</div><div class="truncate text-p-sm text-ink-gray-5">{{ item.value }}</div></div>
      </template>
    </MultiSelect>
    <p v-if="!docname" class="text-p-sm text-ink-gray-5">Select a CRM record to find eligible users.</p>
    <p v-if="error" class="rv-error" role="alert">{{ error }}</p>
  </section>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { MultiSelect } from 'frappe-ui'
import { api } from '../services/api.js'
const props = defineProps({ modelValue: { type: Array, required: true }, doctype: String, docname: String })
const emit = defineEmits(['update:modelValue'])
const rows = ref([]), busy = ref(false), error = ref('')
let generation = 0
const options = computed(() => {
  const existing = new Set(rows.value.map((row) => row.name))
  return [...rows.value, ...props.modelValue.filter((name) => !existing.has(name)).map((name) => ({ name }))]
    .map((user) => ({ label: user.full_name || user.name, value: user.name }))
})
async function load() {
  const current = ++generation
  if (!props.docname) { rows.value = []; busy.value = false; return }
  busy.value = true; error.value = ''
  try { const result = await api('visits.assignees', { reference_doctype: props.doctype, reference_name: props.docname }, 'GET'); if (current === generation) rows.value = result }
  catch (e) { if (current === generation) error.value = e.message } finally { if (current === generation) busy.value = false }
}
function opened(value) { if (value && !rows.value.length && !busy.value) load() }
watch(() => [props.doctype, props.docname], () => { rows.value = []; load() }, { immediate: true })
</script>
