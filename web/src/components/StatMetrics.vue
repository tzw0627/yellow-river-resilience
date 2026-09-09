<script setup lang="ts">
import { computed } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { formatNumber } from "../utils/format";

const store = useResilienceStore();

const meta = computed(() => store.selectedLayerMeta);
const stat = computed(() => store.timelineStat(store.year, store.layer));
const availability = computed(() => store.availability(store.layer, store.year));

const validRatioValue = computed(() => {
  const s = stat.value;
  const ratio = (s?.validRatio ?? s?.valid_ratio) as number | undefined;
  return ratio;
});

const description = computed(() => {
  const m = meta.value;
  if (!m) return "";
  if (store.layer !== "ri" && !availability.value.available) {
    const config = availability.value.config;
    const years = config ? Object.keys(config.years || {}).join("、") : "--";
    return `${m.description} 该图层暂无 ${store.year} 年已转换数据；真实数据源年份：${years}。`;
  }
  const s = stat.value;
  if (!s) return `${m.description} 当前年份暂无统计结果。`;
  const sourceYear = s.sourceYear as number | undefined;
  return `${m.description}${sourceYear && sourceYear !== store.year ? ` 当前年份使用 ${sourceYear} 年可用数据替代。` : ""}`;
});

const hasStat = computed(() => Boolean(stat.value && (store.layer === "ri" || availability.value.available)));
</script>

<template>
  <section class="analysis-summary">
    <div class="analysis-kicker"><span>LIVE SITUATION</span><b>实时态势</b></div>
    <div class="metric-header">
      <span>{{ meta?.label ?? store.layer }}</span>
      <strong>{{ store.year }}<small>年</small></strong>
    </div>
    <p class="layer-description">{{ description }}</p>
  </section>

  <div class="metric-grid">
    <div class="metric-tile">
      <span>中位数</span>
      <strong>{{ hasStat ? formatNumber(stat?.median) : "--" }}</strong>
      <em>Median</em>
    </div>
    <div class="metric-tile">
      <span>P90</span>
      <strong>{{ hasStat ? formatNumber(stat?.p90) : "--" }}</strong>
      <em>高值阈</em>
    </div>
    <div class="metric-tile">
      <span>最小值</span>
      <strong>{{ hasStat ? formatNumber(stat?.min) : "--" }}</strong>
      <em>Min</em>
    </div>
    <div class="metric-tile">
      <span>最大值</span>
      <strong>{{ hasStat ? formatNumber(stat?.max) : "--" }}</strong>
      <em>Max</em>
    </div>
  </div>

  <div class="availability">
    <div class="availability-bar">
      <span :style="{ width: hasStat && validRatioValue != null ? Math.min(100, validRatioValue * 100) + '%' : '0%' }" />
    </div>
    <div class="availability-text">
      <span>有效像元比例</span>
      <strong>{{ hasStat && validRatioValue != null ? Math.round(validRatioValue * 1000) / 10 + "%" : "--" }}</strong>
    </div>
  </div>
</template>
