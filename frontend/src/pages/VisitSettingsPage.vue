<template>
  <LayoutHeader>
    <template #left-header><h1 class="reckon-title">Visit Settings</h1></template>
  </LayoutHeader>
  <main class="reckon-settings"><VisitSettings /></main>
</template>

<script setup>
import LayoutHeader from '@/components/LayoutHeader.vue'
import VisitSettings from '../components/VisitSettings.vue'
</script>

<style scoped>
.reckon-title { font-size:16px; font-weight:600; }
.reckon-settings { display:flex; flex:1; min-width:0; overflow:auto; }
.reckon-settings :deep(.rv-card) { width:100%; max-width:900px; margin:24px; }
</style>
