<script setup lang="ts">
import { computed } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { legendConfig } from "../config";

const store = useResilienceStore();
const config = computed(() => legendConfig[store.layer]);
</script>

<template>
  <div class="dynamic-legend">
    <template v-if="config && config.type === 'gradient'">
      <div class="legend-heading">{{ config.title }}</div>
      <div class="gradient-legend" :style="{ '--legend-gradient': config.gradient }"><span /></div>
      <div class="legend-scale">
        <span>{{ config.low }}</span>
        <span>{{ config.high }}</span>
      </div>
      <div class="legend-notes">
        <span v-for="note in config.notes" :key="note">{{ note }}</span>
      </div>
    </template>
    <template v-else-if="config && config.type === 'categories'">
      <div class="legend-heading">{{ config.title }}</div>
      <div class="category-legend">
        <div v-for="item in config.items" :key="item[1]" class="category-item">
          <span :style="{ background: item[0] }" />
          <strong>{{ item[1] }}</strong>
        </div>
      </div>
    </template>
  </div>
</template>
