<script setup lang="ts">
import { computed } from "vue";
import { storeToRefs } from "pinia";
import { CASE_LAYERS } from "../config";
import { useResilienceStore } from "../stores/resilience";

const store = useResilienceStore();
const { selectedRegionId } = storeToRefs(store);

const cityGroups = computed(() =>
  Array.from(new Set(store.regionCases.map((region) => region.city))).map((city) => ({
    city,
    regions: store.regionCases.filter((region) => region.city === city),
  })),
);

const layerButtons = [
  { id: "four_dim_fri", label: "FRI", title: "洪水风险" },
  { id: "four_dim_er", label: "ER", title: "综合韧性" },
  { id: "four_dim_erd", label: "ERD", title: "密度韧性" },
];

const selectedRegion = computed(() => (store.selectedRegionId ? store.selectedRegion : null));

function onRegionChange(event: Event) {
  const target = event.target as HTMLSelectElement;
  store.setSelectedRegion(target.value);
}
</script>

<template>
  <div class="region-case">
    <label class="field-label" for="region-case-select">管理范围</label>
    <select
      id="region-case-select"
      v-model="selectedRegionId"
      class="region-select"
      :disabled="store.regionCases.length === 0"
      @change="onRegionChange"
    >
      <option value="">黄河滩区中下游（整体）</option>
      <optgroup v-for="group in cityGroups" :key="group.city" :label="group.city">
        <option v-for="region in group.regions" :key="region.id" :value="region.id">
          {{ region.name }}（{{ region.adminCode }}）
        </option>
      </optgroup>
    </select>
    <span class="region-count">{{ store.regionCases.length ? `已加载 ${store.regionCases.length} 个上传边界区县` : "正在读取上传边界区县…" }}</span>

    <div class="case-summary">
      <strong>{{ selectedRegion ? `${selectedRegion.city} · ${selectedRegion.name}` : "黄河滩区中下游整体" }}</strong>
      <span>选择区县后，三维降雨沙盘会固定到该管理单元。</span>
    </div>

    <button type="button" class="case-run-button" :disabled="!store.selectedRegionId" @click="store.startLinkedRiskCase">
      启动韧性-风险联动研判
    </button>

    <div class="case-layer-row" aria-label="核查图层">
      <button
        v-for="item in layerButtons"
        :key="item.id"
        type="button"
        :class="{ active: CASE_LAYERS.includes(store.layer) && store.layer === item.id }"
        :title="item.title"
        @click="store.openCaseLayer(item.id)"
      >
        {{ item.label }}
      </button>
    </div>
  </div>
</template>
