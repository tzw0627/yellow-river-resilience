<script setup lang="ts">
import { computed } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { highlightedTeachingTargets } from "../composables/teachingState";
import { formatNumber } from "../utils/format";

const store = useResilienceStore();

const layerNames: Record<string, string> = {
  four_dim_fri: "FRI 洪水风险",
  four_dim_er: "ER 综合韧性",
  four_dim_erd: "ERD 密度韧性",
  four_dim_erf: "ERF 洪水韧性",
  water: "Water 水体",
  ntl: "NTL 夜间灯光",
  clcd: "CLCD 土地利用",
  gdp: "GDP 空间强度",
  ndvi: "NDVI 植被覆盖",
  evi: "EVI 植被活力",
};

interface Finding {
  key: string;
  title: string;
  detail: string;
  severity: number;
  layer: string;
}

const region = computed(() => store.selectedRegion);
const analysis = computed(() => store.selectedRegionAnalysis);

function stat(layer: string, year = 2024, field: "mean" | "median" | "p90" = "median") {
  return analysis.value?.stats?.[layer]?.[String(year)]?.[field] ?? null;
}

function delta(layer: string, field: "mean" | "median" = "median") {
  const now = stat(layer, 2024, field);
  const before = stat(layer, 2020, field);
  return now != null && before != null ? now - before : null;
}

function rankText(key: string, direction: "high" | "low" = "high") {
  const rank = analysis.value?.ranks?.[key];
  if (!rank) return "";
  const order = direction === "high" ? rank.rank_desc : rank.rank_asc;
  return `28 个区县中第 ${order}`;
}

function pct(value: number | null | undefined) {
  if (value == null) return "--";
  return `${Math.round(value * 1000) / 10}%`;
}

const indicators = computed(() => {
  const a = analysis.value;
  if (!a) return [];
  return [
    {
      layer: "four_dim_fri",
      label: "洪水风险",
      value: stat("four_dim_fri"),
      sub: `${rankText("fri_median_2024", "high")}｜2020-2024 ${formatNumber(delta("four_dim_fri"))}`,
    },
    {
      layer: "four_dim_er",
      label: "综合韧性",
      value: stat("four_dim_er"),
      sub: `${rankText("er_median_2024", "low")}｜2020-2024 ${formatNumber(delta("four_dim_er"))}`,
    },
    {
      layer: "four_dim_erd",
      label: "密度韧性",
      value: stat("four_dim_erd"),
      sub: `${rankText("erd_median_2024", "low")}｜2020-2024 ${formatNumber(delta("four_dim_erd"))}`,
    },
    {
      layer: "water",
      label: "水体频率",
      value: a.derived.water_frequency_ratio_2024,
      percent: true,
      sub: `${rankText("water_frequency_ratio", "high")}｜2020-2024 ${pct(a.derived.water_frequency_delta)}`,
    },
  ];
});

const findings = computed<Finding[]>(() => {
  const a = analysis.value;
  if (!a) return [];
  const d = a.derived;
  const r = a.ranks ?? {};
  const list: Finding[] = [];
  const overlap = d.low_resilience_high_risk_ratio ?? 0;

  if (overlap > 0 || (r.fri_median_2024?.percentile ?? 0) > 0.7 || (r.er_median_2024?.percentile ?? 1) < 0.3) {
    list.push({
      key: "overlap",
      title: "低韧性-高风险叠置",
      detail: `边界内叠置比例为 ${pct(overlap)}；FRI 中位数 ${formatNumber(stat("four_dim_fri"))}，ER 中位数 ${formatNumber(stat("four_dim_er"))}。`,
      severity: overlap * 100 + (r.fri_median_2024?.percentile ?? 0) * 20 + (1 - (r.er_median_2024?.percentile ?? 1)) * 15,
      layer: "four_dim_fri",
    });
  }

  const built = d.built_ratio_2024;
  const builtDelta = d.built_ratio_delta;
  if ((built ?? 0) > 0.18 || (builtDelta ?? 0) > 0.02 || (r.built_ratio?.percentile ?? 0) > 0.65) {
    list.push({
      key: "built",
      title: "建设用地压力",
      detail: `建设用地占比 ${pct(built)}，2020-2024 变化 ${pct(builtDelta)}；${rankText("built_ratio", "high")}。`,
      severity: (built ?? 0) * 55 + Math.max(0, builtDelta ?? 0) * 120 + (r.built_ratio?.percentile ?? 0) * 20,
      layer: "clcd",
    });
  }

  const water = d.water_frequency_ratio_2024;
  if ((water ?? 0) > 0.45 || (r.water_frequency_ratio?.percentile ?? 0) > 0.65) {
    list.push({
      key: "water",
      title: "低洼水体敏感",
      detail: `水体频率较高像元占比 ${pct(water)}，2020-2024 变化 ${pct(d.water_frequency_delta)}；${rankText("water_frequency_ratio", "high")}。`,
      severity: (water ?? 0) * 45 + (r.water_frequency_ratio?.percentile ?? 0) * 20,
      layer: "water",
    });
  }

  const ntlDelta = d.ntl_delta_mean;
  if ((ntlDelta ?? 0) > 0.8 || (r.ntl_delta?.percentile ?? 0) > 0.7) {
    list.push({
      key: "ntl",
      title: "人类活动增强",
      detail: `夜间灯光均值 2020-2024 增加 ${formatNumber(ntlDelta)}；${rankText("ntl_delta", "high")}。`,
      severity: Math.max(0, ntlDelta ?? 0) * 4 + (r.ntl_delta?.percentile ?? 0) * 25,
      layer: "ntl",
    });
  }

  const gdpDelta = d.gdp_delta_mean;
  if ((gdpDelta ?? 0) > 0 || (r.gdp_delta?.percentile ?? 0) > 0.75) {
    list.push({
      key: "gdp",
      title: "经济活动强度变化",
      detail: `GDP 空间强度均值 2020-2024 变化 ${formatNumber(gdpDelta)}；${rankText("gdp_delta", "high")}。`,
      severity: Math.max(0, r.gdp_delta?.percentile ?? 0) * 18,
      layer: "gdp",
    });
  }

  const ndviDelta = d.ndvi_delta_mean;
  if ((ndviDelta ?? 0) < -0.01 || (r.ndvi_delta?.percentile ?? 1) < 0.25) {
    list.push({
      key: "ndvi",
      title: "植被支撑减弱",
      detail: `NDVI 均值 2020-2024 变化 ${formatNumber(ndviDelta)}，需要结合 EVI 与土地利用复核。`,
      severity: Math.abs(Math.min(0, ndviDelta ?? 0)) * 100 + (1 - (r.ndvi_delta?.percentile ?? 1)) * 12,
      layer: "ndvi",
    });
  }

  if (!list.length) {
    list.push({
      key: "stable",
      title: "综合压力不突出",
      detail: `该区县 2024 年 FRI 中位数为 ${formatNumber(stat("four_dim_fri"))}，低韧性高风险叠置比例为 ${pct(overlap)}，建议作为对照样区持续跟踪。`,
      severity: 1,
      layer: "four_dim_fri",
    });
  }

  return list.sort((a, b) => b.severity - a.severity).slice(0, 4);
});

const diagnosis = computed(() => {
  const top = findings.value[0];
  if (!analysis.value || !top) return "正在读取选中区县的分区统计结果。";
  return `${region.value.city}${region.value.name}的主要信号是“${top.title}”。本结论只使用该区县边界内像元统计，不采用全黄河滩区汇总值。`;
});

const priorityAreas = computed(() => {
  const keys = new Set(findings.value.map((item) => item.key));
  const areas: string[] = [];
  if (keys.has("overlap")) areas.push("FRI 高值与 ER/ERD 低值叠置的边界内斑块");
  if (keys.has("built")) areas.push("建设用地比例较高或扩张明显的近河边缘");
  if (keys.has("water")) areas.push("水体频率较高的低洼地带、坑塘和行洪通道周边");
  if (keys.has("ntl") || keys.has("gdp")) areas.push("夜间灯光或经济强度上升的人类活动增强区域");
  if (keys.has("ndvi")) areas.push("NDVI 下降且韧性指标偏弱的生态支撑斑块");
  return areas.slice(0, 4);
});

const measures = computed(() => {
  const keys = new Set(findings.value.map((item) => item.key));
  const items: string[] = [];
  if (keys.has("overlap")) items.push("优先复核低韧性且高风险叠置单元，作为治理解释和现场核查清单的第一层。");
  if (keys.has("built")) items.push("对建设扩张边缘叠加 CLCD 与 FRI/ERD，区分存量建设压力和新增扩张压力。");
  if (keys.has("water")) items.push("对高水体频率低洼地保留行洪、蓄滞和生态缓冲空间。");
  if (keys.has("ntl") || keys.has("gdp")) items.push("对人类活动增强区域补充夜间灯光、GDP 与人口暴露核查，评估风险暴露增量。");
  if (keys.has("ndvi")) items.push("对植被支撑减弱区域补充 NDVI/EVI 截图，核查裸地化、耕地扰动或水分胁迫。");
  if (!items.length) items.push("作为对照区保留年度跟踪，重点观察 FRI、ER 和 ERD 是否出现同步恶化。");
  return items;
});

const verifyLayers = computed(() => {
  const ids = new Set(["four_dim_fri", "four_dim_er", "four_dim_erd"]);
  findings.value.forEach((finding) => ids.add(finding.layer));
  return Array.from(ids);
});
</script>

<template>
  <div class="case-analysis-card region-analysis-only">
    <div class="case-card-header">
      <div>
        <div class="group-title">选中区域分析</div>
        <strong>{{ region.city }} · {{ region.name }}</strong>
      </div>
      <span>{{ store.serviceScenario === "governance" ? "治理服务" : "教学服务" }}</span>
    </div>

    <template v-if="analysis">
      <p class="case-lead">{{ diagnosis }}</p>

      <div class="region-indicator-grid">
        <button
          v-for="item in indicators"
          :key="item.layer"
          type="button"
          class="evidence-tile"
          :class="{ active: store.layer === item.layer }"
          @click="store.openCaseLayer(item.layer)"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.percent ? pct(item.value) : formatNumber(item.value) }}</strong>
          <em>{{ item.sub }}</em>
        </button>
      </div>

      <div class="case-section">
        <div class="group-title">重点区域</div>
        <ul>
          <li v-for="item in priorityAreas" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div class="case-section">
        <div class="group-title">主要影响因素</div>
        <div class="factor-list">
          <button
            v-for="item in findings"
            :key="item.key"
            type="button"
            class="factor-item"
            :class="{ 'teaching-risk-highlight': highlightedTeachingTargets.riskIdentification && item.key === 'overlap' }"
            @click="store.openCaseLayer(item.layer)"
          >
            <strong>{{ item.title }}</strong>
            <span>{{ item.detail }}</span>
          </button>
        </div>
      </div>

      <div class="case-section">
        <div class="group-title">可核查图层</div>
        <div class="verify-layer-list">
          <button
            v-for="layer in verifyLayers"
            :key="layer"
            type="button"
            :class="{ active: store.layer === layer }"
            @click="store.openCaseLayer(layer)"
          >
            {{ layerNames[layer] ?? layer }}
          </button>
        </div>
      </div>

      <div class="case-section">
        <div class="group-title">建议措施</div>
        <ul>
          <li v-for="item in measures" :key="item">{{ item }}</li>
        </ul>
      </div>
    </template>

    <p v-else class="case-lead">正在加载该区县边界内的分区统计结果。</p>
  </div>
</template>
