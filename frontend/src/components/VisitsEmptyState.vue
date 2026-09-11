<template>
  <section class="reckon-empty" aria-labelledby="reckon-visits-heading">
    <div class="reckon-visit-icon"><VisitIcon /></div>
    <h2 id="reckon-visits-heading">No visits found.</h2>
    <p>Schedule your first visit.</p>
    <p class="reckon-phase-note">Visit scheduling will be available in the next release.</p>
  </section>
</template>

<script setup>
import VisitIcon from './VisitIcon.vue'
</script>

<style scoped>
.reckon-empty { display: flex; flex: 1; min-height: 260px; flex-direction: column;
  align-items: center; justify-content: center; padding: 32px 20px; text-align: center; }
.reckon-visit-icon { width: 52px; height: 52px; padding: 13px; border-radius: 16px;
  background: var(--surface-gray-2, #f3f5f4); color: var(--ink-gray-6, #4b625b); }
h2 { margin: 18px 0 8px; font-size: 18px; font-weight: 600; color: var(--ink-gray-9, #172824); }
p { margin: 0; color: var(--ink-gray-6, #5d6965); font-size: 14px; }
.reckon-phase-note { margin-top: 16px; max-width: 290px; font-size: 12px; line-height: 1.6; }
</style>
