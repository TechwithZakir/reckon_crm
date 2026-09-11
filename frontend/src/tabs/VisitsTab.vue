<template><VisitsEmptyState /></template>

<script setup>
import VisitsEmptyState from '../components/VisitsEmptyState.vue'
defineProps({ doctype: { type: String, required: true }, docname: { type: String, required: true } })
</script>
