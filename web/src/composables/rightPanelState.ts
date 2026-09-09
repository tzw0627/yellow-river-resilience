import { ref } from "vue";

export type RightPanelTab = "analysis" | "emergency" | "agent" | "report";

export const activeRightPanelTab = ref<RightPanelTab>("emergency");
