<script setup lang="ts">
import { computed, onMounted } from "vue";
import { useResilienceStore } from "./stores/resilience";
import ResizableLayout from "./components/ResizableLayout.vue";
import SidePanel from "./components/SidePanel.vue";
import MapStage from "./components/MapStage.vue";
import RightPanel from "./components/RightPanel.vue";

const store = useResilienceStore();
const boundsLabel = computed(() => {
  const b = store.bounds;
  if (!b) return "研究区范围：112.18°E–116.68°E / 34.24°N–36.45°N";
  return `研究区范围：${b.west.toFixed(2)}°E–${b.east.toFixed(2)}°E / ${b.south.toFixed(2)}°N–${b.north.toFixed(2)}°N`;
});

onMounted(() => {
  void store.init();
});
</script>

<template>
  <main class="app-shell">
    <div class="cockpit-frame">
      <header class="cockpit-topbar" aria-label="平台标题栏">
        <div class="competition-lockup">
          <span class="competition-index">YR</span>
          <span class="competition-copy">
            <small>YELLOW RIVER DIGITAL TWIN</small>
            <strong>黄河数字孪生运营平台</strong>
          </span>
        </div>
        <div class="topbar-title-block">
          <span class="topbar-kicker">Yellow River Resilience · Digital Twin</span>
          <h1><b>黄河智韧</b><span>黄河中下游滩区生态韧性数字孪生与遥感智能体平台</span></h1>
        </div>
        <div class="topbar-meta" aria-label="当前状态">
          <span class="online-dot">系统在线</span>
          <span>{{ store.year }} 态势快照</span>
        </div>
        <div class="topbar-context" aria-label="项目数据概况">
          <span><b>50</b> 项多源数据</span>
          <span><b>6</b> 期时序</span>
          <span><b>250 m</b> 统一网格</span>
          <span class="topbar-extent">{{ boundsLabel }}</span>
        </div>
      </header>

      <div v-if="store.error" class="load-error">数据加载失败：{{ store.error }}</div>
      <ResizableLayout v-else>
        <template #left>
          <SidePanel />
        </template>
        <template #center>
          <MapStage />
        </template>
        <template #right>
          <RightPanel />
        </template>
      </ResizableLayout>
    </div>
  </main>
</template>

<style scoped>
.load-error {
  padding: 20px;
  color: #ffb4a2;
}
</style>
