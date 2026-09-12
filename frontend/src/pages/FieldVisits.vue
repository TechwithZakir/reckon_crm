<template>
  <LayoutHeader>
    <template #left-header><h1 class="reckon-title">Field Visits</h1></template>
  </LayoutHeader>
  <main class="reckon-visits"><VisitWorkspace /></main>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import VisitWorkspace from '../components/VisitWorkspace.vue'
</script>

<style scoped>
.reckon-title { font-size: 16px; font-weight: 600; }
.reckon-visits { display: flex; flex: 1; min-width: 0; overflow: auto; }
</style>
