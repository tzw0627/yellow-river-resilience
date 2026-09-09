<script setup lang="ts">
import StatMetrics from "./StatMetrics.vue";
import CaseAnalysis from "./CaseAnalysis.vue";
import TwinPanel from "./TwinPanel.vue";
import TimelineChart from "./TimelineChart.vue";
import QueryResult from "./QueryResult.vue";
import EmergencyPanel from "./EmergencyPanel.vue";
import ReportPanel from "./ReportPanel.vue";
import { highlightedTeachingTargets } from "../composables/teachingState";
import { activeRightPanelTab as tab } from "../composables/rightPanelState";

type Tab = "analysis" | "emergency" | "report";
</script>

<template>
  <aside class="metric-panel">
    <div class="panel-tabs">
      <button class="panel-tab" :class="{ active: tab === 'analysis' }" @click="tab = 'analysis'"><b>01</b> 综合态势</button>
      <button class="panel-tab" :class="{ active: tab === 'emergency' }" @click="tab = 'emergency'"><b>02</b> 应急指挥</button>
      <button class="panel-tab" :class="{ active: tab === 'report', 'teaching-report-tab-highlight': highlightedTeachingTargets.reportGenerate }" @click="tab = 'report'"><b>03</b> 成果报告</button>
    </div>

    <template v-if="tab === 'analysis'">
      <StatMetrics />
      <CaseAnalysis />
      <TwinPanel />
      <div class="timeline-card">
        <div class="group-title">时间序列（中位数）</div>
        <TimelineChart />
      </div>
      <div class="query-card">
        <div class="group-title">点击查询</div>
        <QueryResult />
      </div>
    </template>

    <EmergencyPanel v-else-if="tab === 'emergency'" />
    <ReportPanel v-else />
  </aside>
</template>
