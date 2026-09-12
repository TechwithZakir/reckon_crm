<template><VisitWorkspace :doctype="doctype" :docname="docname" /></template>

<script setup>
import VisitWorkspace from '../components/VisitWorkspace.vue'
defineProps({ doctype: { type: String, required: true }, docname: { type: String, required: true } })
</script>
