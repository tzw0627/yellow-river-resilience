<script setup lang="ts">
import { computed, reactive, ref, watch } from "vue";
import { useResilienceStore } from "../stores/resilience";
import RegionSelector from "./RegionSelector.vue";
import {
  architectureTree,
  layerColors,
  layerKeyToId,
  realDataLayer,
  realDataYearEntry,
  absoluteSourceText,
} from "../config";
import {
  boundaryOnlyMode,
  showOnlyBoundaryMode,
  showThematicLayerMode,
  studyAreaBoundaryVisible,
  toggleStudyAreaBoundary,
} from "../composables/layerDisplayMode";
import {
  isResilienceLayer,
  resilienceAssessmentLayerExpanded,
  setActiveDashboardModule,
  setSelectedDashboardLayer,
} from "../composables/resilienceDashboardState";
import {
  activeLearningTaskId,
  activeTeachingTask,
  addLearningEvidence,
  floatingTeachingHintLoadingPrompt,
  handleTeachingTaskClick,
  highlightedTeachingTargets,
  learningEvidenceItems,
  removeLearningEvidence,
  requestTeachingHint,
  showLearningEvidenceList,
  taskStatusMap,
  teachingPromptLabels,
  teachingTasks,
  toggleLearningEvidenceList,
  type TeachingTask,
  type TeachingTaskStatus,
  type TeachingPromptType,
} from "../composables/teachingState";
import type { TreeItem, TreeModule } from "../config/types";
import { activeRightPanelTab } from "../composables/rightPanelState";

const store = useResilienceStore();

const openState = reactive<Record<string, boolean>>(
  Object.fromEntries(architectureTree.map((m) => [m.id, false])),
);
const boundaryModeOpen = ref(false);
const educationSubSections = reactive<Record<string, boolean>>({
  regionalCase: false,
  teachingTasks: false,
  aiTutor: false,
  evidenceReport: false,
});

watch(
  () => openState["resilience-assessment"],
  (expanded) => {
    resilienceAssessmentLayerExpanded.value = Boolean(expanded);
  },
  { immediate: true },
);

watch(activeLearningTaskId, (taskId) => {
  if (taskId === "step_3_lulc_vegetation_water_interpretation") {
    openState["remote-sensing-twin"] = true;
  }
  if (taskId === "step_4_er_fri_analysis") {
    openState["resilience-assessment"] = true;
  }
  if (taskId === "step_5_learning_report") {
    openState["service-layer"] = true;
    educationSubSections.evidenceReport = true;
  }
});

const educationSubSectionItems = [
  {
    id: "regionalCase",
    title: "区域治理与教学案例",
    subtitle: "区域选择、案例分析与治理服务",
  },
  {
    id: "teachingTasks",
    title: "教学任务链",
    subtitle: "五步任务引导",
  },
  {
    id: "aiTutor",
    title: "AI助教提示",
    subtitle: "概念·方法·证据核验",
  },
  {
    id: "evidenceReport",
    title: "证据栏与学习报告",
    subtitle: "证据记录与报告生成",
  },
];

const teachingHintButtons: { promptType: TeachingPromptType; title: string }[] = [
  { promptType: "concept_hint", title: "解释概念，不直接给结论" },
  { promptType: "method_hint", title: "提示下一步分析方法" },
  { promptType: "evidence_check", title: "核查证据是否充分" },
];

const taskStatusLabel: Record<TeachingTaskStatus, string> = {
  not_started: "未开始",
  in_progress: "进行中",
  completed: "已完成",
};

const savedEvidenceCount = computed(() => learningEvidenceItems.value.length);

function addCurrentEvidence() {
  const stat = store.timelineStat(store.year, store.layer);
  const region = store.selectedRegionId ? store.selectedRegion : null;
  const task = activeTeachingTask.value;
  addLearningEvidence({
    learning_task_id: activeLearningTaskId.value ?? "",
    taskTitle: task?.title ?? "未选择",
    year: store.year,
    region: region ? [region.city, region.name].filter(Boolean).join(" / ") || region.name || "黄河滩区" : "未选择",
    region_id: store.selectedRegionId,
    layer: store.selectedLayerMeta?.label ?? store.layer,
    layer_id: store.layer,
    summaryStats: stat ? { ...stat } : null,
    selectedPoint: store.query ? { ...store.query } : null,
    agentHint: task?.prompt ?? "",
    studentNote: "",
  });
  showLearningEvidenceList.value = true;
}

function evidenceLocationText(item: { selectedPoint: Record<string, unknown> | null; agentHint: string }) {
  if (!item.selectedPoint) return item.agentHint;
  const place = typeof item.selectedPoint.place === "string" ? item.selectedPoint.place : "";
  const lon = typeof item.selectedPoint.lon === "number" ? item.selectedPoint.lon.toFixed(4) : "--";
  const lat = typeof item.selectedPoint.lat === "number" ? item.selectedPoint.lat.toFixed(4) : "--";
  return `点击位置：${place || `${lon}, ${lat}`}`;
}

function moduleIdForDashboard(moduleId: string) {
  if (moduleId === "remote-sensing-twin") return "data";
  if (moduleId === "resilience-assessment") return "resilience";
  if (moduleId === "service-layer") return "emergency";
  return "other";
}

function openEmergencyPanel() {
  activeRightPanelTab.value = "emergency";
  store.setYear(2020);
  store.setLayer("four_dim_fri");
  showThematicLayerMode();
  setActiveDashboardModule("emergency", "实测降水应急研判");
  setSelectedDashboardLayer("four_dim_fri");
}

function toggle(id: string) {
  openState[id] = !openState[id];
  const module = architectureTree.find((item) => item.id === id);
  setActiveDashboardModule(moduleIdForDashboard(id), module?.title ?? "");
}

function activateBoundaryOnlyMode() {
  setActiveDashboardModule("boundary", "\u4ec5\u8fb9\u754c\u6a21\u5f0f");
  setSelectedDashboardLayer("");
  showOnlyBoundaryMode();
}

function toggleChinaBoundaryVisible() {
  setActiveDashboardModule("china-boundary", "\u4e2d\u56fd\u56fd\u754c");
  store.setChinaBoundaryVisible(!store.chinaBoundaryVisible);
}

function toggleBoundaryModeOpen() {
  boundaryModeOpen.value = !boundaryModeOpen.value;
}

function toggleEducationSubSection(id: string) {
  setActiveDashboardModule("education", "\u6559\u80b2\u4ea4\u4e92/\u670d\u52a1\u5c42");
  educationSubSections[id] = !educationSubSections[id];
}

function selectTeachingTask(task: TeachingTask) {
  setActiveDashboardModule("education", "\u6559\u80b2\u4ea4\u4e92/\u670d\u52a1\u5c42");
  store.setServiceScenario("teaching");
  if (task.id === "step_2_year_layer_selection") store.setYear(2024);
  if (task.id === "step_3_lulc_vegetation_water_interpretation") openState["remote-sensing-twin"] = true;
  if (task.id === "step_4_er_fri_analysis") openState["resilience-assessment"] = true;
  if (task.id === "step_5_learning_report") {
    openState["service-layer"] = true;
    educationSubSections.evidenceReport = true;
  }
  handleTeachingTaskClick(task);
}

function sendTeachingHint(promptType: TeachingPromptType) {
  setActiveDashboardModule("education", "\u6559\u80b2\u4ea4\u4e92/\u670d\u52a1\u5c42");
  store.setServiceScenario("teaching");
  requestTeachingHint(promptType);
}

interface LeafView {
  className: string;
  color: string;
  typeLabel: string;
}

function leafView(item: TreeItem): LeafView {
  const layerId = item.layerId || layerKeyToId[item.key];
  const dataKey = item.dataKey || item.key;
  const dataConfig = realDataLayer(dataKey);
  const isLayer = item.type === "layer" && !!layerId;
  const isData = item.type === "data";
  const active = isLayer && layerId === store.layer;
  const availability = isLayer
    ? store.availability(layerId!)
    : dataConfig
      ? store.availability(dataKey)
      : null;
  const hasYear = Boolean(availability?.entry || dataConfig?.years?.static);
  const converted = Boolean(availability?.available || dataConfig?.years?.static?.converted);

  const highlighted = highlightedTeachingTargets.layerKeys.includes(dataKey) || (layerId ? highlightedTeachingTargets.layerKeys.includes(layerId) : false);

  const className = [
    "tree-leaf",
    active ? "active" : "",
    highlighted ? "teaching-layer-highlight" : "",
    isLayer || isData ? "" : "pending",
    hasYear && !converted ? "needs-conversion" : "",
  ]
    .filter(Boolean)
    .join(" ");

  const color = isLayer ? layerColors[layerId!] || "var(--muted)" : "var(--line)";
  const typeLabel = isLayer
    ? converted
      ? "图层"
      : "待转换"
    : isData
      ? hasYear
        ? "真实数据"
        : "缺年份"
      : "占位";

  return { className, color, typeLabel };
}

function showRealDataNotice(item: TreeItem, reason = "") {
  const dataKey = item.dataKey || item.key;
  const config = realDataLayer(dataKey);
  if (!config) {
    store.setNotice(`${item.label}｜${item.message || "功能正在建设中。"}`);
    return;
  }
  const entry = realDataYearEntry(dataKey, store.year) || config.years?.static || null;
  const yearKeys = Object.keys(config.years || {}).join("、") || "静态/表格";
  const source = absoluteSourceText(entry?.source || config.source || config.statsCsv || config.sourceFolder);
  const status =
    reason ||
    (entry?.converted === false || config.converted === false
      ? "该真实数据尚未转换为 Cesium 可直接加载的瓦片/PNG。"
      : "该真实数据已登记。");
  store.setNotice(
    `${config.label}｜可用年份：${yearKeys}；格式：${config.format}；分辨率：${config.resolution}\n真实路径：${source}\n${status}`,
  );
}

function clickLeaf(item: TreeItem, moduleId = "") {
  const layerId = item.layerId || layerKeyToId[item.key];
  const dashboardModuleId = isResilienceLayer(layerId) ? "resilience" : moduleIdForDashboard(moduleId);
  const module = architectureTree.find((entry) => entry.id === moduleId);
  setActiveDashboardModule(dashboardModuleId, module?.title ?? "");
  setSelectedDashboardLayer(layerId || item.dataKey || item.key);
  if (item.type === "layer" && layerId) {
    showThematicLayerMode();
    const availability = store.availability(layerId);
    if (!availability.available && layerId !== "ri") {
      store.setLayer(layerId);
      showRealDataNotice(
        item,
        "该图层暂无当前年份已转换数据，地图不加载假数据。请先将对应 GeoTIFF 转为 PNG/XYZ 瓦片。",
      );
      return;
    }
    store.setLayer(layerId);
    store.setNotice(null);
    return;
  }
  showRealDataNotice(item);
}

defineProps<{ modules?: TreeModule[] }>();
</script>

<template>
  <div class="layer-tree">
    <section class="tree-module layer-switch-module boundary-mode-module" :class="boundaryModeOpen ? 'open' : 'collapsed'">
      <button
        type="button"
        class="tree-module-header layer-switch-header boundary-mode-header"
        :class="{ active: boundaryOnlyMode }"
        :aria-pressed="boundaryOnlyMode"
        :aria-expanded="boundaryModeOpen"
        @click="activateBoundaryOnlyMode"
      >
        <span
          class="tree-arrow boundary-collapse-arrow"
          role="button"
          tabindex="0"
          :aria-label="boundaryModeOpen ? '收起仅边界模式' : '展开仅边界模式'"
          @click.stop="toggleBoundaryModeOpen"
          @keydown.enter.stop.prevent="toggleBoundaryModeOpen"
          @keydown.space.stop.prevent="toggleBoundaryModeOpen"
        >
          {{ boundaryModeOpen ? "▾" : "▸" }}
        </span>
        <span class="tree-module-index boundary-status">{{ boundaryOnlyMode ? "ON" : "OFF" }}</span>
        <span class="tree-module-title">
          <strong>仅边界模式</strong>
          <em>卫星底图 + 研究区边界</em>
        </span>
      </button>
      <div v-show="boundaryModeOpen" class="tree-module-body boundary-mode-body">
        <button
          type="button"
          class="tree-leaf boundary-control"
          :class="{ active: studyAreaBoundaryVisible }"
          :style="{ '--layer-color': studyAreaBoundaryVisible ? '#00eaff' : 'rgba(157, 184, 207, 0.45)' }"
          :aria-pressed="studyAreaBoundaryVisible"
          @click="toggleStudyAreaBoundary"
        >
          <span class="tree-leaf-dot" />
          <span class="tree-leaf-label">研究区边界</span>
          <span class="tree-leaf-type">{{ studyAreaBoundaryVisible ? "显示" : "隐藏" }}</span>
        </button>
        <p class="boundary-mode-help">只显示卫星底图和研究区边界，不加载专题填充图层。</p>
      </div>
    </section>

    <section class="tree-module layer-switch-module">
      <button
        type="button"
        class="tree-module-header layer-switch-header"
        :aria-pressed="store.chinaBoundaryVisible"
        @click="toggleChinaBoundaryVisible"
      >
        <span class="tree-arrow">{{ store.chinaBoundaryVisible ? "✓" : "○" }}</span>
        <span class="tree-module-index">ON</span>
        <span class="tree-module-title">
          <strong>中国国界</strong>
          <em>{{ store.chinaBoundaryVisible ? "默认显示，点击隐藏" : "已隐藏，点击显示" }}</em>
        </span>
      </button>
    </section>

    <section
      v-for="(module, index) in architectureTree"
      :key="module.id"
      class="tree-module"
      :class="openState[module.id] ? 'open' : 'collapsed'"
    >
      <button
        type="button"
        class="tree-module-header"
        :aria-expanded="openState[module.id]"
        @click="toggle(module.id)"
      >
        <span class="tree-arrow">{{ openState[module.id] ? "▾" : "▸" }}</span>
        <span class="tree-module-index">0{{ index + 1 }}</span>
        <span class="tree-module-title">
          <strong>{{ module.title }}</strong>
          <em>{{ module.subtitle }}</em>
        </span>
      </button>

      <div v-show="openState[module.id]" class="tree-module-body">
        <div v-for="category in module.categories" :key="category.title" class="tree-category">
          <template v-if="module.id === 'service-layer'">
            <div class="emergency-entry-card">
              <span class="emergency-entry-tag"><i /> OBSERVED DATA</span>
              <strong>实测降水应急研判</strong>
              <p>19 个沿线国家站 · 366 天逐日记录 · 1954—2019 历史基线</p>
              <small>强降水识别 → FRI/ERF 风险叠加 → 重点站点核查</small>
              <button type="button" @click="openEmergencyPanel">进入降水研判</button>
            </div>
          </template>
          <template v-else>
            <div class="tree-category-title">{{ category.title }}</div>
            <div class="tree-leaf-list">
            <button
              v-for="item in category.items"
              :key="item.key"
              type="button"
              :class="leafView(item).className"
              :style="{ '--layer-color': leafView(item).color }"
              @click="clickLeaf(item, module.id)"
            >
              <span class="tree-leaf-dot" />
              <span class="tree-leaf-label">{{ item.label }}</span>
              <span class="tree-leaf-type">{{ leafView(item).typeLabel }}</span>
            </button>
          </div>
          </template>
        </div>
      </div>
    </section>
  </div>
</template>
