<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { storeToRefs } from "pinia";
import { useResilienceStore } from "../stores/resilience";
import { CesiumMap, type ClickResult } from "../cesium/CesiumMap";
import { nearestStation } from "../config";
import { explainValue } from "../utils/format";
import { boundaryOnlyMode, studyAreaBoundaryVisible } from "../composables/layerDisplayMode";
import {
  setActiveDashboardModule,
  setSelectedDashboardLayer,
  shouldShowResilienceDashboard,
} from "../composables/resilienceDashboardState";
import { studyAreaOverviewRequest } from "../composables/teachingState";
import {
  emergencyActive,
  emergencyMapStations,
  selectedEmergencyDate,
  selectedEmergencyDay,
} from "../composables/emergencyState";
import FloatingAgentBall from "./FloatingAgentBall.vue";
import LegendPanel from "./LegendPanel.vue";
import ResilienceDashboardOverlay from "./ResilienceDashboardOverlay.vue";

const store = useResilienceStore();
const { year, layer, bounds, selectedRegionId, caseActive } = storeToRefs(store);

const container = ref<HTMLElement | null>(null);
const viewport = ref<HTMLElement | null>(null);
const presentation = ref(false);
let map: CesiumMap | null = null;
let initialized = false;

const activeLayerLabel = computed(() => store.selectedLayerMeta?.label ?? store.layer);

function extentLabel(): string {
  if (store.caseActive) {
    const region = store.selectedRegion;
    return `${region.city} · ${region.name}｜${region.bounds.west.toFixed(2)}°E-${region.bounds.east.toFixed(2)}°E / ${region.bounds.south.toFixed(2)}°N-${region.bounds.north.toFixed(2)}°N`;
  }
  const b = store.bounds;
  if (!b) return "加载中";
  return `${b.west.toFixed(2)}°E-${b.east.toFixed(2)}°E / ${b.south.toFixed(2)}°N-${b.north.toFixed(2)}°N`;
}

async function onMapClick(result: ClickResult) {
  const b = store.bounds;
  if (!b) return;
  if (result.lon < b.west || result.lon > b.east || result.lat < b.south || result.lat > b.north) {
    store.setNotice("研究区外｜请点击黄河滩区河南段范围内。");
    return;
  }
  try {
    const grid = await store.loadQueryGrid();
    const value = store.sampleQueryGrid(grid, result.lon, result.lat);
    const place = nearestStation(result.lon, result.lat)?.name ?? "研究区";
    store.setQuery({
      lon: result.lon,
      lat: result.lat,
      value,
      place,
      explanation: explainValue(store.layer, value),
    });
  } catch (err) {
    store.setNotice(`查询失败｜${err instanceof Error ? err.message : String(err)}`);
  }
}

function refreshOverlay() {
  if (!map) return;
  map.setStudyAreaBoundaryVisible(studyAreaBoundaryVisible.value);
  if (boundaryOnlyMode.value) {
    map.clearThematicLayer();
    return;
  }
  const overlay = store.currentOverlay();
  void map.updateThematicLayer({
    layer: store.layer,
    year: store.year,
    overlayUrl: overlay.url,
    categorical: overlay.categorical,
    rectangle: overlay.rectangle ?? undefined,
  });
}

function tryInit() {
  if (initialized || !container.value || !store.bounds) return;
  map = new CesiumMap();
  map.init(container.value, store.bounds, onMapClick);
  map.setChinaBoundaryVisible(store.chinaBoundaryVisible);
  map.setStudyAreaBoundaryVisible(studyAreaBoundaryVisible.value);
  map.setSelectedRegionBoundary(store.caseActive ? store.selectedRegion.feature : null);
  initialized = true;
  refreshOverlay();
  map.setPrecipitationStations(emergencyMapStations.value);
  if (emergencyActive.value) map.setEmergencyPresentationMode(true, emergencyViewBounds());
}

function onResize() {
  map?.resize();
}

function togglePresentation() {
  presentation.value = !presentation.value;
  document.body.classList.toggle("presentation-mode", presentation.value);
  setTimeout(() => {
    map?.resize();
    map?.setViewToStudyArea();
  }, 120);
}

function toggleChinaBoundary() {
  setActiveDashboardModule("china-boundary", "\u4e2d\u56fd\u56fd\u754c");
  setSelectedDashboardLayer("");
  store.setChinaBoundaryVisible(!store.chinaBoundaryVisible);
}

function flyToSelectedRegion() {
  if (!map) return;
  map.setSelectedRegionBoundary(store.selectedRegion.feature);
  map.flyChinaToStudyArea(store.selectedRegion.bounds, 0.9);
}

function emergencyViewBounds() {
  return store.selectedRegionId ? store.selectedRegion.bounds : store.bounds;
}

onMounted(() => {
  tryInit();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  map?.destroy();
});

watch(bounds, () => tryInit());
watch([year, layer], () => refreshOverlay());
watch(selectedRegionId, (id) => {
  map?.setSelectedRegionBoundary(id ? store.selectedRegion.feature : null);
  if (emergencyActive.value) {
    map?.setEmergencyPresentationMode(true, emergencyViewBounds());
  } else if (id) {
    flyToSelectedRegion();
  }
});
watch(
  () => store.regionCases.length,
  () => map?.setSelectedRegionBoundary(store.caseActive ? store.selectedRegion.feature : null),
);
watch(caseActive, (active) => {
  if (active && !emergencyActive.value) flyToSelectedRegion();
});
watch(
  () => store.chinaBoundaryVisible,
  (visible) => map?.setChinaBoundaryVisible(visible),
);
watch(boundaryOnlyMode, () => refreshOverlay());
watch(studyAreaBoundaryVisible, (visible) => map?.setStudyAreaBoundaryVisible(visible));
watch(emergencyMapStations, (stations) => map?.setPrecipitationStations(stations), { deep: true });
watch(emergencyActive, (active) => map?.setEmergencyPresentationMode(active, emergencyViewBounds()));
watch(studyAreaOverviewRequest, (request) => {
  if (!request || !map) return;
  map.setSelectedRegionBoundary(null);
  map.flyChinaToStudyArea(store.bounds, 0.9);
});
</script>

<template>
  <section class="map-stage" :class="{ 'emergency-map-mode': emergencyActive }">
    <div class="map-toolbar">
      <div class="map-situation-copy">
        <span class="toolbar-kicker">{{ emergencyActive ? "03 · 实测降水三维沙盘" : "03 · 空间态势研判" }}</span>
        <strong>{{ store.selectedRegionId ? `${store.selectedRegion.city} · ${store.selectedRegion.name}` : "黄河中下游滩区 · 整体" }}</strong>
        <small>{{ extentLabel() }}</small>
      </div>
      <div class="toolbar-actions">
        <span class="map-live-status"><i />{{ emergencyActive ? selectedEmergencyDate : `${store.year} · ${activeLayerLabel}` }}</span>
        <button v-if="!emergencyActive" class="mode-button boundary-toggle" :class="{ off: !store.chinaBoundaryVisible }" @click="toggleChinaBoundary">
          国界 {{ store.chinaBoundaryVisible ? "ON" : "OFF" }}
        </button>
        <button v-if="!emergencyActive" class="mode-button" @click="togglePresentation">
          {{ presentation ? "退出全景" : "全景展示" }}
        </button>
        <button class="icon-button" title="回到完整研究区" aria-label="回到完整研究区" @click="map?.setViewToStudyArea()">⌖</button>
      </div>
    </div>
    <div ref="viewport" class="map-viewport">
      <div ref="container" class="cesium-container" />
      <ResilienceDashboardOverlay v-if="shouldShowResilienceDashboard" :map-container="viewport" />
      <div v-if="emergencyActive" class="rainfall-map-badge">
        <span>OBSERVED PRECIPITATION</span>
        <strong>{{ selectedEmergencyDate }}</strong>
        <small>峰值 {{ selectedEmergencyDay?.peak.toFixed(1) ?? "0.0" }} mm · 蓝柱高度随实测雨量变化</small>
      </div>
      <FloatingAgentBall v-else />
    </div>
    <div class="map-legend" :class="{ 'boundary-only': boundaryOnlyMode }">
      <div class="legend-title-row">
        <span class="legend-swatch boundary" />
        <strong>04 · 图例与证据判读</strong>
      </div>
      <p v-if="emergencyActive" class="legend-mode-note">蓝色立柱表示站点实测降水量，柱体高度按雨量统一放大；底面为当前风险或韧性图层。</p>
      <p v-else-if="boundaryOnlyMode" class="legend-mode-note">仅显示卫星影像底图与研究区边界；点击左侧专题图层后加载数据覆盖层。</p>
      <LegendPanel v-else />
    </div>
  </section>
</template>
