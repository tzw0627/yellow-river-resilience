<script setup lang="ts">
import { storeToRefs } from "pinia";
import { useResilienceStore } from "../stores/resilience";

const store = useResilienceStore();
const { year } = storeToRefs(store);
</script>

<template>
  <div class="year-track">
    <button
      v-for="y in store.availableYears"
      :key="y"
      class="year-button"
      :class="{ active: y === year }"
      @click="store.setYear(y)"
    >
      {{ y }}
    </button>
  </div>
</template>
