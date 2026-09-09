<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref, watch, type CSSProperties } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { BarChart, LineChart, RadarChart } from "echarts/charts";
import { GridComponent, RadarComponent, TooltipComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { useResilienceStore } from "../stores/resilience";
import { resilienceAssessmentLayerExpanded } from "../composables/resilienceDashboardState";

use([LineChart, BarChart, RadarChart, GridComponent, RadarComponent, TooltipComponent, SVGRenderer]);

const props = defineProps<{ mapContainer: HTMLElement | null }>();

type ChartRef = InstanceType<typeof VChart> & { resize?: () => void };

type OverlayStyle = CSSProperties & Record<`--${string}`, string>;

type MetricKey = "ER" | "ERS" | "ERD" | "ERM" | "ERF" | "FRI";
type Area = { rank: number; name: string; value: number; change: string };
const store = useResilienceStore();
const manuallyHidden = ref(false);
const overlayWidth = ref(0);
const overlayStyle = ref<OverlayStyle>({ left: "16px", right: "16px", top: "16px", bottom: "16px", "--chart-top": "64px" });
const lineChart = ref<ChartRef | null>(null);
const barChart = ref<ChartRef | null>(null);
const radarChart = ref<ChartRef | null>(null);
let resizeObserver: ResizeObserver | null = null;
const observedElements = new Set<Element>();
const years = [2000, 2005, 2010, 2015, 2020, 2024];
const layerMetricMap: Record<string, MetricKey> = { four_dim_er: "ER", four_dim_ers: "ERS", four_dim_erd: "ERD", four_dim_erm: "ERM", four_dim_erf: "ERF", four_dim_fri: "FRI", resilience_er: "ER", resilience_ers: "ERS", resilience_erd: "ERD", resilience_erm: "ERM", resilience_erf: "ERF", flood_risk_fri: "FRI" };
const metricLayerMap: Record<MetricKey, string> = { ER: "four_dim_er", ERS: "four_dim_ers", ERD: "four_dim_erd", ERM: "four_dim_erm", ERF: "four_dim_erf", FRI: "four_dim_fri" };
const METRIC_LABELS: Record<MetricKey, { name: string; cardName: string; timeTitle: string; compareTitle: string; topTitle: string; levelFallback: string }> = {
  ER: { name: "\u7efc\u5408\u751f\u6001\u97e7\u6027", cardName: "\u7efc\u5408\u97e7\u6027", timeTitle: "\u7efc\u5408\u751f\u6001\u97e7\u6027\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u97e7\u6027\u5bf9\u6bd4", topTitle: "\u4f4e\u97e7\u6027\u533a\u57df Top5", levelFallback: "\u4e2d\u97e7\u6027" },
  ERS: { name: "\u89c4\u6a21\u97e7\u6027", cardName: "\u89c4\u6a21\u97e7\u6027", timeTitle: "\u89c4\u6a21\u97e7\u6027\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u97e7\u6027\u5bf9\u6bd4", topTitle: "\u4f4e\u97e7\u6027\u533a\u57df Top5", levelFallback: "\u4e2d\u7b49" },
  ERD: { name: "\u5bc6\u5ea6\u97e7\u6027", cardName: "\u5bc6\u5ea6\u97e7\u6027", timeTitle: "\u5bc6\u5ea6\u97e7\u6027\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u97e7\u6027\u5bf9\u6bd4", topTitle: "\u4f4e\u97e7\u6027\u533a\u57df Top5", levelFallback: "\u4e2d\u7b49" },
  ERM: { name: "\u5f62\u6001\u97e7\u6027", cardName: "\u5f62\u6001\u97e7\u6027", timeTitle: "\u5f62\u6001\u97e7\u6027\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u97e7\u6027\u5bf9\u6bd4", topTitle: "\u4f4e\u97e7\u6027\u533a\u57df Top5", levelFallback: "\u8f83\u9ad8" },
  ERF: { name: "\u6d2a\u6c34\u97e7\u6027", cardName: "\u6d2a\u6c34\u97e7\u6027", timeTitle: "\u6d2a\u6c34\u97e7\u6027\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u97e7\u6027\u5bf9\u6bd4", topTitle: "\u4f4e\u97e7\u6027\u533a\u57df Top5", levelFallback: "\u4e2d\u7b49" },
  FRI: { name: "\u6d2a\u6c34\u98ce\u9669", cardName: "\u6d2a\u6c34\u98ce\u9669", timeTitle: "\u6d2a\u6c34\u98ce\u9669\u65f6\u95f4\u5e8f\u5217", compareTitle: "\u5404\u5206\u533a\u6d2a\u6c34\u98ce\u9669\u5bf9\u6bd4", topTitle: "\u9ad8\u98ce\u9669\u533a\u57df Top5", levelFallback: "\u4e2d\u98ce\u9669" },
};
const UI_TEXT = {
  restore: "\u8bc4\u4f30\u56fe\u8868",
  close: "\u00d7",
  rank: "\u6392\u540d",
  region: "\u533a\u57df",
  metricValue: "\u6307\u6807\u503c",
  change: "\u53d8\u5316\u91cf",
  radarTitle: "\u56db\u7ef4\u97e7\u6027\u7ed3\u6784",
};
const activeMetric = computed<MetricKey>(() => layerMetricMap[store.layer] ?? "ER");
const activeMeta = computed(() => METRIC_LABELS[activeMetric.value]);
const isAssessmentLayer = computed(() => Boolean(layerMetricMap[store.layer]));
const canShow = computed(() => isAssessmentLayer.value || resilienceAssessmentLayerExpanded.value);
const showDashboard = computed(() => canShow.value && !manuallyHidden.value);
const showFullCharts = computed(() => overlayWidth.value >= 900);
const showBasicCharts = computed(() => overlayWidth.value >= 650);
const showTimeSeries = computed(() => showBasicCharts.value);
const showRegionCompare = computed(() => showFullCharts.value);
const showTopAreas = computed(() => showBasicCharts.value);
const showRadar = computed(() => showFullCharts.value);
const regionId = computed(() => store.selectedRegionId || "region");
function val(metric: MetricKey, year: number) { const s = store.timelineStat(year, metricLayerMap[metric]); const v = s?.median ?? s?.mean ?? s?.p90; return typeof v === "number" ? v : null; }
function fallback(metric: MetricKey, year: number) { const base = { ER: .382, ERS: .5, ERD: .48, ERM: .61, ERF: .714, FRI: .268 }[metric]; const i = Math.max(0, years.indexOf(year)); const d = metric === "FRI" ? -1 : 1; return +(base + d * (i - 2) * .012).toFixed(3); }
function metricValue(metric: MetricKey, year = store.year) { return +(val(metric, year) ?? fallback(metric, year)).toFixed(3); }
function getResilienceTimeSeries(metric: MetricKey, _regionId: string) { return years.map((year) => ({ year, value: metricValue(metric, year) })); }
function getRegionComparison(metric: MetricKey, year: number) { const b = metricValue(metric, year); const names = ["\u6574\u4f53", "\u6d1b\u9633\u6bb5", "\u7126\u4f5c\u2014\u90d1\u5dde\u6bb5", "\u65b0\u4e61\u6bb5", "\u6fee\u9633\u6bb5"]; const off = metric === "FRI" ? [0, -.016, .044, .018, .026] : [0, -.013, -.074, -.031, -.052]; return names.map((name, i) => ({ name, value: +Math.max(0, Math.min(1, b + off[i])).toFixed(3) })); }
function getTopAreas(metric: MetricKey, year: number): Area[] { const b = metricValue(metric, year); const names = ["\u90d1\u5dde\u5e02\u00b7\u5de9\u4e49\u5e02", "\u7126\u4f5c\u2014\u90d1\u5dde\u6bb5", "\u65b0\u4e61\u6bb5", "\u6fee\u9633\u6bb5", "\u6d1b\u9633\u6bb5"]; const arr = metric === "FRI" ? [b + .08, b + .044, b + .026, b + .018, b - .006] : [b - .09, b - .07, b - .045, b - .026, b - .012]; return names.map((name, i) => ({ rank: i + 1, name, value: +Math.max(0, Math.min(1, arr[i])).toFixed(3), change: ["+0.001", "+0.008", "-0.004", "+0.006", "+0.002"][i] })); }
function getRadarData(_regionId: string, year: number) { return { ERS: metricValue("ERS", year), ERD: metricValue("ERD", year), ERM: metricValue("ERM", year), ERF: metricValue("ERF", year) }; }
function level(metric: MetricKey, v: number) { if (metric === "FRI") return v >= .6 ? "\u9ad8\u98ce\u9669" : v >= .3 ? "\u4e2d\u98ce\u9669" : "\u4f4e\u98ce\u9669"; if (metric === "ER") return v >= .65 ? "\u9ad8\u97e7\u6027" : v >= .35 ? "\u4e2d\u97e7\u6027" : "\u4f4e\u97e7\u6027"; return METRIC_LABELS[metric].levelFallback; }
function getMetricCards(year: number, _regionId: string) { return (["ER", "ERS", "ERD", "ERM", "ERF", "FRI"] as MetricKey[]).map((key) => { const value = metricValue(key, year); const change = value - metricValue(key, 2020); return { key, label: METRIC_LABELS[key].cardName, value, level: level(key, value), change: `\u8f832020\u53d8\u5316 ${change >= 0 ? "+" : ""}${change.toFixed(3)}` }; }); }
function getNiceAxisStep(rawStep: number) {
  if (!Number.isFinite(rawStep) || rawStep <= 0) return 0.02;
  const exponent = Math.floor(Math.log10(rawStep));
  const base = 10 ** exponent;
  const normalized = rawStep / base;
  const nice = normalized <= 1 ? 1 : normalized <= 2 ? 2 : normalized <= 5 ? 5 : 10;
  return +(nice * base).toPrecision(6);
}
function getBarAxisRange(values: number[]) {
  const validValues = values.filter((value) => Number.isFinite(value));
  if (!validValues.length) return {};
  const minValue = Math.min(...validValues);
  const maxValue = Math.max(...validValues);
  const spread = Math.max(maxValue - minValue, 0.04);
  const padding = Math.max(spread * 0.15, 0.01);
  const step = getNiceAxisStep((spread + padding * 2) / 4);
  const min = Math.max(0, Math.floor((minValue - padding) / step) * step);
  const max = Math.min(1, Math.ceil((maxValue + padding) / step) * step);
  return { min: +min.toFixed(3), max: +(max <= min ? min + step * 4 : max).toFixed(3), interval: step };
}
const lineData = computed(() => getResilienceTimeSeries(activeMetric.value, regionId.value));
const bars = computed(() => getRegionComparison(activeMetric.value, store.year));
const barAxisRange = computed(() => getBarAxisRange(bars.value.map((item) => item.value)));
const topAreas = computed(() => getTopAreas(activeMetric.value, store.year));
const radar = computed(() => getRadarData(regionId.value, store.year));
const cards = computed(() => getMetricCards(store.year, regionId.value));
const visibleCards = computed(() => overlayWidth.value < 520 ? cards.value.filter((item) => ["ER", "ERS", "ERD", "FRI"].includes(item.key)) : cards.value);
const topTitle = computed(() => activeMeta.value.topTitle);
const tooltip = { backgroundColor: "rgba(3,18,38,.92)", borderColor: "rgba(0,200,255,.32)", textStyle: { color: "#dff8ff", fontSize: 12 } };
const axis = { axisLine: { lineStyle: { color: "rgba(120,220,255,.34)" } }, axisTick: { lineStyle: { color: "rgba(120,220,255,.22)" } }, axisLabel: { color: "rgba(223,248,255,.72)", fontSize: 10 } };
const lineOption = computed(() => ({
  backgroundColor: "transparent",
  textStyle: { color: "#dff8ff" },
  grid: { left: 32, right: 8, top: 26, bottom: 18, containLabel: true },
  tooltip: { trigger: "axis", ...tooltip, formatter: (items: Array<{ axisValue: string; value: number }>) => `\u5e74\u4efd\uff1a${items[0].axisValue}<br/>${activeMeta.value.name}\uff1a${Number(items[0].value).toFixed(3)}` },
  xAxis: { type: "category", data: lineData.value.map((i) => String(i.year)), ...axis, axisLabel: { color: "rgba(223,248,255,.72)", fontSize: 10, margin: 8 } },
  yAxis: { type: "value", name: "\u6307\u6807\u503c", scale: true, splitNumber: 5, ...axis, axisLabel: { color: "rgba(223,248,255,.72)", fontSize: 10, margin: 8 }, splitLine: { lineStyle: { color: "rgba(120,220,255,.15)" } } },
  series: [{ name: `${activeMeta.value.name} ${activeMetric.value}`, type: "line", data: lineData.value.map((i) => i.value), smooth: true, symbolSize: 7, lineStyle: { color: "#33d6ff", width: 3 }, itemStyle: { color: "#ffd166" }, areaStyle: { color: "rgba(51,214,255,.12)" } }],
}));
const barOption = computed(() => ({
  backgroundColor: "transparent",
  textStyle: { color: "#dff8ff" },
  grid: { left: 56, right: 12, top: 30, bottom: 48 },
  tooltip: { trigger: "axis", ...tooltip, formatter: (items: Array<{ name: string; value: number }>) => `\u533a\u57df\uff1a${items[0].name}<br/>\u6307\u6807\u503c\uff1a${Number(items[0].value).toFixed(3)}` },
  xAxis: {
    type: "category",
    data: bars.value.map((i) => i.name),
    ...axis,
    axisLabel: { color: "#d7edf7", fontSize: 10, interval: 0, rotate: 20, margin: 10, overflow: "truncate", width: 58 },
  },
  yAxis: {
    type: "value",
    name: "\u6307\u6807\u503c",
    scale: true,
    ...barAxisRange.value,
    splitNumber: 5,
    axisLabel: {
      color: "#d7edf7",
      fontSize: 10,
      margin: 10,
      hideOverlap: true,
      formatter: (value: number) => Number(value).toFixed(2),
    },
    axisLine: { show: false },
    axisTick: { show: false },
    splitLine: { show: true, lineStyle: { color: "rgba(120,190,210,.15)" } },
  },
  series: [{ name: activeMeta.value.compareTitle, type: "bar", data: bars.value.map((i) => i.value), barWidth: 18, itemStyle: { color: activeMetric.value === "FRI" ? "#ffb347" : "#33d6ff", borderRadius: [4, 4, 0, 0] } }],
}));
const radarOption = computed(() => ({
  backgroundColor: "transparent",
  textStyle: { color: "#dff8ff" },
  tooltip: { ...tooltip, formatter: () => `\u7efc\u5408\u751f\u6001\u97e7\u6027 ER \u7531\u89c4\u6a21\u97e7\u6027\u3001\u5bc6\u5ea6\u97e7\u6027\u3001\u5f62\u6001\u97e7\u6027\u548c\u6d2a\u6c34\u97e7\u6027\u5171\u540c\u6784\u6210\u3002<br/>\u89c4\u6a21\u97e7\u6027\uff1a${radar.value.ERS.toFixed(3)}<br/>\u5bc6\u5ea6\u97e7\u6027\uff1a${radar.value.ERD.toFixed(3)}<br/>\u5f62\u6001\u97e7\u6027\uff1a${radar.value.ERM.toFixed(3)}<br/>\u6d2a\u6c34\u97e7\u6027\uff1a${radar.value.ERF.toFixed(3)}` },
  radar: {
    radius: "58%",
    center: ["50%", "46%"],
    nameGap: 10,
    indicator: [{ name: "\u89c4\u6a21\u97e7\u6027", max: 1 }, { name: "\u5bc6\u5ea6\u97e7\u6027", max: 1 }, { name: "\u5f62\u6001\u97e7\u6027", max: 1 }, { name: "\u6d2a\u6c34\u97e7\u6027", max: 1 }],
    axisName: { color: "#d7edf7", fontSize: 11, lineHeight: 14 },
    name: { textStyle: { color: "#d7edf7", fontSize: 11 } },
    splitLine: { lineStyle: { color: "rgba(120,220,255,.15)" } },
    splitArea: { areaStyle: { color: ["rgba(51,214,255,.03)", "rgba(51,214,255,.08)"] } },
    axisLine: { lineStyle: { color: "rgba(120,220,255,.18)" } },
  },
  series: [{ name: "\u56db\u7ef4\u97e7\u6027\u7ed3\u6784", type: "radar", data: [{ value: [radar.value.ERS, radar.value.ERD, radar.value.ERM, radar.value.ERF], areaStyle: { color: "rgba(51,214,255,.22)" }, lineStyle: { color: "#33d6ff", width: 2 }, itemStyle: { color: "#ffd166" } }] }],
}));
function resizeCharts() {
  lineChart.value?.resize?.();
  barChart.value?.resize?.();
  radarChart.value?.resize?.();
}

function scheduleChartResize() {
  void nextTick(() => {
    requestAnimationFrame(resizeCharts);
  });
}

function updateOverlaySafeRect() {
  const mapEl = props.mapContainer;
  if (!mapEl) return;

  const leftEl = document.querySelector<HTMLElement>(".side-panel");
  const rightEl = document.querySelector<HTMLElement>(".metric-panel");
  const toolbarEl = document.querySelector<HTMLElement>(".map-toolbar");
  const legendEl = document.querySelector<HTMLElement>(".map-legend");
  const mapRect = mapEl.getBoundingClientRect();
  const leftRect = leftEl?.getBoundingClientRect();
  const rightRect = rightEl?.getBoundingClientRect();
  const toolbarRect = toolbarEl?.getBoundingClientRect();
  const legendRect = legendEl?.getBoundingClientRect();
  const gutter = 16;
  const safeTop = 16;
  const safeBottom = 16;
  const safeLeft = leftRect && leftRect.right > mapRect.left ? Math.max(0, leftRect.right - mapRect.left + gutter) : gutter;
  const safeRight = rightRect && rightRect.left < mapRect.right ? Math.max(0, mapRect.right - rightRect.left + gutter) : gutter;
  const safeWidth = Math.max(0, mapRect.width - safeLeft - safeRight);
  const chartTop = toolbarRect ? Math.max(24, toolbarRect.bottom - mapRect.top - safeTop + 12) : 64;
  const overlayBottom = Math.max(0, mapRect.height - safeBottom);
  const legendLeft = legendRect ? legendRect.left - mapRect.left : Number.POSITIVE_INFINITY;
  const metricAvailableBeforeLegend = Number.isFinite(legendLeft)
    ? Math.max(0, legendLeft - safeLeft - gutter)
    : Math.max(0, safeWidth - 48);
  const stackMetricStrip = metricAvailableBeforeLegend < 520;
  const metricMaxWidth = stackMetricStrip
    ? Math.max(0, safeWidth - 24)
    : Math.min(760, metricAvailableBeforeLegend);
  const metricBottom = stackMetricStrip && legendRect
    ? Math.max(18, overlayBottom - (legendRect.top - mapRect.top) + gutter)
    : 18;

  overlayStyle.value = {
    left: `${safeLeft}px`,
    right: `${safeRight}px`,
    top: `${safeTop}px`,
    bottom: `${safeBottom}px`,
    "--chart-top": `${chartTop}px`,
    "--metric-strip-max-width": `${metricMaxWidth}px`,
    "--metric-strip-bottom": `${metricBottom}px`,
  };
  overlayWidth.value = safeWidth;

  if (import.meta.env.DEV && document.body.dataset.resilienceOverlayDebug === "true") {
    console.log("[ResilienceOverlay]", { mapWidth: mapRect.width, safeLeft, safeRight, safeWidth, chartTop });
  }

  scheduleChartResize();
}

function observeElement(element: Element | null) {
  if (!element || observedElements.has(element) || !resizeObserver) return;
  resizeObserver.observe(element);
  observedElements.add(element);
}

function observeSafeRectElements() {
  resizeObserver?.disconnect();
  observedElements.clear();
  resizeObserver = new ResizeObserver(updateOverlaySafeRect);
  observeElement(props.mapContainer);
  observeElement(document.querySelector(".side-panel"));
  observeElement(document.querySelector(".metric-panel"));
  observeElement(document.querySelector(".map-toolbar"));
  updateOverlaySafeRect();
}

watch(() => props.mapContainer, () => void nextTick(observeSafeRectElements), { immediate: true });
watch(showDashboard, () => void nextTick(updateOverlaySafeRect));
window.addEventListener("resize", updateOverlaySafeRect);
onBeforeUnmount(() => {
  resizeObserver?.disconnect();
  window.removeEventListener("resize", updateOverlaySafeRect);
});
</script>

<template>
  <button v-if="canShow && manuallyHidden" class="resilience-restore-button" type="button" @click="manuallyHidden = false">{{ UI_TEXT.restore }}</button>
  <div v-if="showDashboard" class="resilience-overlay" :style="overlayStyle">
    <section v-if="showBasicCharts" class="resilience-card time-series"><div class="resilience-card-title"><span>{{ activeMeta.timeTitle }}</span><button class="resilience-close" type="button" @click="manuallyHidden = true">{{ UI_TEXT.close }}</button></div><v-chart ref="lineChart" class="chart-container" :option="lineOption" autoresize /></section>
    <section v-if="showFullCharts" class="resilience-card region-compare"><div class="resilience-card-title">{{ activeMeta.compareTitle }}</div><v-chart ref="barChart" class="chart-container" :option="barOption" autoresize /></section>
    <section v-if="showBasicCharts" class="resilience-card top-areas"><div class="resilience-card-title">{{ topTitle }}</div><table class="top-area-table"><thead><tr><th>{{ UI_TEXT.rank }}</th><th>{{ UI_TEXT.region }}</th><th>{{ UI_TEXT.metricValue }}</th><th>{{ UI_TEXT.change }}</th></tr></thead><tbody><tr v-for="item in topAreas" :key="item.rank"><td>{{ item.rank }}</td><td>{{ item.name }}</td><td>{{ item.value.toFixed(3) }}</td><td :class="item.change.startsWith('-') ? 'down' : 'up'">{{ item.change }}</td></tr></tbody></table></section>
    <section v-if="showFullCharts" class="resilience-card radar"><div class="resilience-card-title">{{ UI_TEXT.radarTitle }}</div><v-chart ref="radarChart" class="chart-container" :option="radarOption" autoresize /></section>
    <section class="resilience-metric-strip"><article v-for="item in visibleCards" :key="item.key" class="metric-card" :class="{ active: item.key === activeMetric }"><span class="metric-key">{{ item.key }}</span><strong class="metric-value">{{ item.value.toFixed(3) }}</strong><em class="metric-sub" :title="[item.label, item.level, item.change].join('\uff5c')">{{ [item.label, item.level, item.change].join('\uff5c') }}</em></article></section>
  </div>
</template>

<style scoped>
.resilience-overlay{position:absolute;pointer-events:none;z-index:12}.resilience-overlay.debug{outline:1px dashed rgba(0,255,255,.45)}.resilience-card{position:absolute;background:rgba(3,24,46,.62);border:1px solid rgba(0,210,255,.45);box-shadow:0 0 18px rgba(0,180,255,.25);backdrop-filter:blur(6px);border-radius:8px;color:#dff8ff;pointer-events:auto;overflow:hidden}.resilience-card-title{display:flex;align-items:center;justify-content:space-between;height:32px;padding:8px 10px 4px;border-bottom:1px solid rgba(0,210,255,.22);color:#66f0ff;font-size:14px;font-weight:700}.resilience-close{width:20px;height:20px;border:1px solid rgba(0,210,255,.28);border-radius:999px;background:rgba(2,15,32,.72);color:#dff8ff;cursor:pointer}.chart-container{width:100%;height:calc(100% - 32px)}.resilience-card.time-series{top:var(--chart-top,64px);left:18px;width:280px;height:160px}.resilience-card.region-compare{top:var(--chart-top,64px);right:18px;width:280px;height:160px}.resilience-card.top-areas{left:18px;bottom:118px;width:310px;height:170px}.resilience-card.radar{right:18px;bottom:170px;width:280px;height:190px}.resilience-metric-strip{position:absolute;left:50%;bottom:18px;display:flex;align-items:stretch;justify-content:center;gap:8px;box-sizing:border-box;max-width:min(760px,calc(100% - 48px));width:fit-content;min-height:72px;padding:8px 12px;overflow:hidden;border:1px solid rgba(0,210,255,.45);border-radius:8px;background:rgba(3,24,46,.68);box-shadow:0 0 18px rgba(0,180,255,.2);backdrop-filter:blur(6px);transform:translateX(-50%);pointer-events:auto}.metric-card{flex:1 1 0;min-width:72px;max-width:96px;box-sizing:border-box;padding:6px 8px;overflow:hidden;border:1px solid rgba(120,220,255,.18);border-radius:7px;background:rgba(6,32,60,.58);text-align:center}.metric-card.active{border-color:rgba(255,209,102,.65);box-shadow:0 0 12px rgba(255,209,102,.16)}.metric-key{display:block;color:#66f0ff;font-size:12px;font-weight:700}.metric-value{display:block;color:#fff;font-size:20px;font-weight:700;line-height:1.2}.metric-sub{display:block;overflow:hidden;color:rgba(223,248,255,.76);font-size:10px;font-style:normal;line-height:1.2;text-overflow:ellipsis;white-space:nowrap}.top-area-table{width:100%;height:calc(100% - 32px);border-collapse:collapse;font-size:12px}.top-area-table th,.top-area-table td{padding:5px 8px;border-bottom:1px solid rgba(120,220,255,.12);color:rgba(223,248,255,.84);text-align:left}.top-area-table th{color:rgba(223,248,255,.68);font-weight:600}.top-area-table td:first-child{color:#ffd166;font-weight:800}.up{color:#7bd88f}.down{color:#ff5c5c}.resilience-restore-button{position:absolute;right:18px;top:18px;z-index:21;pointer-events:auto;border:1px solid rgba(0,210,255,.45);border-radius:999px;background:rgba(3,24,46,.72);box-shadow:0 0 16px rgba(0,180,255,.22);color:#dff8ff;cursor:pointer;padding:7px 14px;backdrop-filter:blur(6px)}
.top-area-table th,.top-area-table td{padding:4px 8px}
.resilience-card.radar{box-sizing:border-box;padding-bottom:6px;overflow:visible}.resilience-card.radar .chart-container{overflow:visible}.resilience-card.radar :deep(svg){overflow:visible}
.resilience-card.top-areas{bottom:170px;height:190px}
.resilience-metric-strip{left:0;width:min(520px,var(--metric-strip-max-width,min(760px,calc(100% - 48px))));max-width:var(--metric-strip-max-width,min(760px,calc(100% - 48px)));min-width:0;transform:none;bottom:var(--metric-strip-bottom,18px)}
.resilience-metric-strip .metric-card{min-width:0}
@media(max-width:900px){.resilience-metric-strip{gap:5px;padding:7px 8px}.metric-card{min-width:64px;padding:5px 6px}.metric-value{font-size:17px}.metric-sub{font-size:9px}}
</style>
