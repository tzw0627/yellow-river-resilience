<script setup lang="ts">
import { computed } from "vue";
import VChart from "vue-echarts";
import { use } from "echarts/core";
import { LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent, MarkPointComponent } from "echarts/components";
import { SVGRenderer } from "echarts/renderers";
import { useResilienceStore } from "../stores/resilience";
import { layerColors } from "../config";

use([LineChart, GridComponent, TooltipComponent, MarkPointComponent, SVGRenderer]);

const store = useResilienceStore();

const series = computed(() =>
  store.availableYears
    .map((y) => ({ year: y, value: store.timelineStat(y, store.layer)?.median as number | undefined }))
    .filter((d) => d.value !== null && d.value !== undefined),
);

const option = computed(() => {
  const color = layerColors[store.layer] || "#1d6f88";
  const data = series.value;
  return {
    grid: { left: 36, right: 16, top: 16, bottom: 24 },
    tooltip: {
      trigger: "axis",
      backgroundColor: "rgba(3, 18, 38, 0.92)",
      borderColor: "rgba(0, 200, 255, 0.28)",
      textStyle: { color: "#e6f8ff", fontSize: 12 },
      extraCssText: "box-shadow:0 10px 24px rgba(0,0,0,.28);backdrop-filter:blur(8px);",
    },
    xAxis: {
      type: "category",
      data: data.map((d) => String(d.year)),
      axisLine: { lineStyle: { color: "rgba(120, 220, 255, 0.34)" } },
      axisTick: { lineStyle: { color: "rgba(120, 220, 255, 0.28)" } },
      axisLabel: { color: "#9fc7db", fontSize: 10 },
    },
    yAxis: {
      type: "value",
      scale: true,
      axisLabel: { color: "#9fc7db", fontSize: 10 },
      splitLine: { lineStyle: { color: "rgba(120, 220, 255, 0.12)" } },
    },
    series: [
      {
        type: "line",
        data: data.map((d) => d.value),
        smooth: true,
        symbolSize: (_: unknown, params: { dataIndex: number }) =>
          data[params.dataIndex]?.year === store.year ? 10 : 6,
        lineStyle: { color, width: 3 },
        itemStyle: { color },
      },
    ],
  };
});

const hasData = computed(() => series.value.length >= 2);
</script>

<template>
  <v-chart v-if="hasData" class="chart-box" :option="option" autoresize />
  <p v-else class="layer-description">当前图层时间序列数据不足。</p>
</template>
