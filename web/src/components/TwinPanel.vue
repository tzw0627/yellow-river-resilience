<script setup lang="ts">
import { computed } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { formatNumber } from "../utils/format";
import type { TwinSegment } from "../config/types";

const store = useResilienceStore();

const objects = computed(() => {
  if (!store.twin) return [] as { id: string; name: string; object: TwinSegment }[];
  return [
    { id: "region", name: "整体", object: store.twin.region },
    ...store.twin.segments.map((segment) => ({ id: segment.id, name: segment.name, object: segment })),
  ];
});

const selected = computed(() => objects.value.find((o) => o.id === store.twinObject) || objects.value[0]);

const stationsText = computed(() => {
  const obj = selected.value?.object;
  if (!obj?.stations?.length || !store.twin) return "全部代表站点";
  return obj.stations
    .map((id) => store.twin!.stations.find((s) => s.id === id)?.name)
    .filter(Boolean)
    .join("、");
});
</script>

<template>
  <div v-if="selected" class="twin-card">
    <div class="group-title">孪生对象状态</div>
    <div class="twin-tabs">
      <button
        v-for="o in objects"
        :key="o.id"
        class="twin-tab"
        :class="{ active: o.id === selected.id }"
        @click="store.setTwinObject(o.id)"
      >
        {{ o.name }}
      </button>
    </div>
    <div class="twin-state">
      <div class="twin-object-title">
        <strong>{{ selected.object.name }}</strong>
        <span>{{ selected.object.type }}</span>
      </div>
      <p>{{ selected.object.description || "黄河滩区中下游整体孪生对象。" }}</p>
      <div class="twin-kpis">
        <div><span>RI</span><strong>{{ formatNumber(selected.object.state.ri.median) }}</strong></div>
        <div><span>NDVI</span><strong>{{ formatNumber(selected.object.state.ndvi.median) }}</strong></div>
        <div><span>EVI</span><strong>{{ formatNumber(selected.object.state.evi.median) }}</strong></div>
        <div><span>状态</span><strong>{{ selected.object.state.summary.level }}</strong></div>
      </div>
      <div class="twin-line"><span>关联站点</span><strong>{{ stationsText }}</strong></div>
      <em>{{ selected.object.state.summary.text }}</em>
    </div>
  </div>
</template>
