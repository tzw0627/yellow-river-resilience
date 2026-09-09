<script setup lang="ts">
import { computed } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { formatNumber } from "../utils/format";

const store = useResilienceStore();
const meta = computed(() => store.selectedLayerMeta);
</script>

<template>
  <div class="query-result">
    <template v-if="store.notice">
      <strong>{{ store.notice.split("｜")[0] }}</strong>
      <span v-for="(line, i) in store.notice.split('｜').slice(1).join('｜').split('\n')" :key="i">{{ line }}</span>
    </template>
    <template v-else-if="store.query">
      <strong>{{ store.query.place }}附近</strong>
      <span>经纬度：{{ store.query.lon.toFixed(4) }}°E，{{ store.query.lat.toFixed(4) }}°N</span>
      <span>{{ meta?.label }}：<b>{{ formatNumber(store.query.value) }}</b></span>
      <em>{{ store.query.explanation }}</em>
    </template>
    <template v-else>
      <strong>请选择场景中的位置</strong>
      <span>点击研究区查看当前图层近似值。</span>
    </template>
  </div>
</template>
