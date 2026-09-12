<template>
  <fieldset class="rv-assignees">
    <legend>Assigned users</legend>
    <div class="rv-actions"><input aria-label="Find assigned users" v-model="search" placeholder="Search name or email" @keydown.enter.prevent="load" /><button type="button" :disabled="busy || !docname" @click="load">Search users</button></div>
    <p v-if="!docname">Select a CRM record to find eligible users.</p>
    <div class="rv-user-options">
      <label v-for="user in choices" :key="user.name" class="rv-check"><input type="checkbox" :checked="modelValue.includes(user.name)" @change="toggle(user.name, $event.target.checked)" />{{ user.full_name || user.name }} <small>{{ user.name }}</small></label>
    </div>
    <p>{{ modelValue.length }} selected · A separate visit is created for each user (maximum 25).</p>
    <p v-if="busy" role="status">Finding users…</p><p v-if="error" class="rv-error" role="alert">{{ error }}</p>
  </fieldset>
</template>
<script setup>
import { computed, ref, watch } from 'vue'
import { api } from '../services/api.js'
const props = defineProps({ modelValue: { type: Array, required: true }, doctype: String, docname: String })
const emit = defineEmits(['update:modelValue'])
const search = ref(''), rows = ref([]), busy = ref(false), error = ref('')
let generation = 0
const choices = computed(() => [...rows.value, ...props.modelValue.filter(name => !rows.value.some(row => row.name === name)).map(name => ({name}))])
function toggle(name, checked) { emit('update:modelValue', checked ? [...new Set([...props.modelValue, name])] : props.modelValue.filter(value => value !== name)) }
async function load() {
  const current = ++generation
  if (!props.docname) { rows.value = []; busy.value = false; return }
  busy.value = true; error.value = ''
  try { const result = await api('visits.assignees', {reference_doctype:props.doctype,reference_name:props.docname,search:search.value}, 'GET'); if (current === generation) rows.value = result }
  catch (e) { if (current === generation) error.value = e.message } finally { if (current === generation) busy.value = false }
}
watch(() => [props.doctype, props.docname], () => { rows.value = []; load() }, { immediate: true })
</script>
