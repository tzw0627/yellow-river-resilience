import { computed, ref } from "vue";

export type ResilienceDashboardModuleId = "data" | "resilience" | "education" | "emergency" | "boundary" | "china-boundary" | "other" | "02" | "";

export const resilienceAssessmentLayerExpanded = ref(false);
export const activeModuleId = ref<ResilienceDashboardModuleId>("");
export const activeModuleName = ref("");
export const selectedLayerId = ref("");

export const RESILIENCE_LAYER_IDS = [
  "ER",
  "ERS",
  "ERD",
  "ERM",
  "ERF",
  "FRI",
  "four_dim_er",
  "four_dim_ers",
  "four_dim_erd",
  "four_dim_erm",
  "four_dim_erf",
  "four_dim_fri",
  "resilience_er",
  "resilience_ers",
  "resilience_erd",
  "resilience_erm",
  "resilience_erf",
  "flood_risk_fri",
];

export function isResilienceLayer(layerId: string | null | undefined) {
  return Boolean(layerId && RESILIENCE_LAYER_IDS.includes(layerId));
}

export function setActiveDashboardModule(moduleId: ResilienceDashboardModuleId, moduleName = "") {
  activeModuleId.value = moduleId;
  activeModuleName.value = moduleName;
  if (moduleId !== "resilience" && moduleId !== "02") {
    selectedLayerId.value = "";
  }
}

export function setSelectedDashboardLayer(layerId: string | null | undefined) {
  selectedLayerId.value = layerId ?? "";
}

export const shouldShowResilienceDashboard = computed(() => {
  return (
    activeModuleId.value === "resilience" ||
    activeModuleId.value === "02" ||
    activeModuleName.value === "\u97e7\u6027\u667a\u80fd\u8bc4\u4f30\u5c42" ||
    isResilienceLayer(selectedLayerId.value)
  );
});
