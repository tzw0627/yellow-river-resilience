import { computed, reactive, ref, watch } from "vue";
import { showOnlyBoundaryMode } from "./layerDisplayMode";
import { activeRightPanelTab } from "./rightPanelState";

export type TeachingTaskStatus = "not_started" | "in_progress" | "completed";
export type TeachingPromptType = "concept_hint" | "method_hint" | "evidence_check";

export interface TeachingTask {
  id: string;
  title: string;
  prompt: string;
}

export interface TeachingTaskCard {
  id: string;
  title: string;
  objective: string;
  operation: string;
  focus: string[];
  requirement: string;
  layerNotes?: string[];
  suggestedActions?: string[];
  thinkingPrompt?: string;
}

export interface LearningEvidenceItem {
  id: string;
  learning_task_id: string;
  taskTitle: string;
  year: number;
  region: string;
  region_id: string;
  layer: string;
  layer_id: string;
  summaryStats: Record<string, unknown> | null;
  selectedPoint: Record<string, unknown> | null;
  agentHint: string;
  studentNote: string;
  createdAt: string;
}

export const teachingTasks: TeachingTask[] = [
  {
    id: "step_1_region_understanding",
    title: "认识研究区",
    prompt:
      "观察黄河中下游滩区的空间范围、边界形态、周边地形、城镇、农田和水体分布。建议默认显示卫星底图和研究区边界，不急于打开专题图层。",
  },
  {
    id: "step_2_year_layer_selection",
    title: "选择年份与图层",
    prompt:
      "选择分析年份，如2000、2005、2010、2015、2020、2024，并选择CLCD、NDVI、EVI、水体、ER、FRI等图层，理解不同图层代表的含义。",
  },
  {
    id: "step_3_lulc_vegetation_water_interpretation",
    title: "判读土地利用/植被/水体变化",
    prompt:
      "对比不同年份土地利用、植被指数和水体分布，观察建设用地扩张、植被变化、水体变化和生态空间变化。",
  },
  {
    id: "step_4_er_fri_analysis",
    title: "分析生态韧性ER与洪水风险FRI关系",
    prompt:
      "同时打开ER和FRI等专题图层，识别低生态韧性、高洪水风险以及二者叠加区域，并结合ERD、ERF等指标解释原因。",
  },
  {
    id: "step_5_learning_report",
    title: "生成学习报告",
    prompt:
      "整理研究区域、年份、使用图层、主要发现、证据截图、统计值、智能体提示和个人结论，并生成“黄河中下游滩区遥感数智学习报告”。",
  },
];

export const activeLearningTaskId = ref<string | null>(null);

export const taskStatusMap = reactive<Record<string, TeachingTaskStatus>>(
  Object.fromEntries(teachingTasks.map((task) => [task.id, "not_started"])),
);

export const activeTeachingTask = computed(() =>
  activeLearningTaskId.value ? teachingTasks.find((task) => task.id === activeLearningTaskId.value) ?? null : null,
);

export const studyAreaOverviewRequest = ref(0);
export const floatingTeachingTipRequest = ref(0);
export const highlightedTeachingTargets = reactive({
  yearSelector: false,
  layerSelector: false,
  layerKeys: [] as string[],
  riskIdentification: false,
  evidenceReport: false,
  reportGenerate: false,
  showEvidenceCount: false,
  yearNote: "",
  layerNote: "",
});

const learningEvidenceStorageKey = "learningEvidenceItems";

function loadLearningEvidenceItems(): LearningEvidenceItem[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(learningEvidenceStorageKey);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as LearningEvidenceItem[]) : [];
  } catch {
    return [];
  }
}

export const learningEvidenceItems = ref<LearningEvidenceItem[]>(loadLearningEvidenceItems());
export const showLearningEvidenceList = ref(false);

watch(
  learningEvidenceItems,
  (items) => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(learningEvidenceStorageKey, JSON.stringify(items));
  },
  { deep: true },
);

export function addLearningEvidence(item: Omit<LearningEvidenceItem, "id" | "createdAt">) {
  learningEvidenceItems.value = [
    {
      ...item,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`,
      createdAt: new Date().toISOString(),
    },
    ...learningEvidenceItems.value,
  ];
}

export function removeLearningEvidence(id: string) {
  learningEvidenceItems.value = learningEvidenceItems.value.filter((item) => item.id !== id);
}

export function toggleLearningEvidenceList() {
  showLearningEvidenceList.value = !showLearningEvidenceList.value;
}

export const floatingTeachingTips: Record<string, string> = {
  step_1_region_understanding:
    "你正在进行第1步“认识研究区”。建议先观察卫星底图和研究区边界，重点关注黄河河道、滩区边界、周边城镇、农田和水体的空间关系。此阶段不建议立即打开专题图层，应先判断研究区的基本空间格局。观察完成后，请用一句话概括该区域的空间特征，并保存为学习证据。",
  step_2_year_layer_selection:
    "你正在进行第2步“选择年份与图层”。请先选择一个分析年份，如2000、2005、2010、2015、2020或2024，再选择CLCD、NDVI、EVI、水体、ER、FRI等专题图层。建议先从2024年和NDVI或CLCD图层开始观察，再切换其他年份进行对比，理解不同图层所表达的生态和风险信息。",
  step_3_lulc_vegetation_water_interpretation:
    "你正在进行第3步“判读土地利用/植被/水体变化”。请对比不同年份的CLCD、NDVI、EVI和水体图层，重点观察建设用地是否扩张、植被覆盖是否变化、水体范围是否发生转移。建议先选择2000年和2024年进行对比，并用一句话描述你观察到的主要变化。",
  step_4_er_fri_analysis:
    "你正在进行第4步“分析生态韧性ER与洪水风险FRI关系”。请同时查看ER和FRI图层，重点识别生态韧性较低、洪水风险较高以及二者叠加的区域。随后结合ERD、ERF等指标，思考这些区域是否与建设用地扩张、地形低洼、水体邻近或生态空间破碎有关。",
  step_5_learning_report:
    "你正在进行第5步“生成学习报告”。请整理本次学习中的研究区域、分析年份、使用图层、主要发现、证据截图、统计值、智能体提示和个人结论，并生成“黄河中下游滩区遥感数智学习报告”。报告中要尽量用图层和数据支撑自己的判断。",
};

export const regionUnderstandingTaskCard: TeachingTaskCard = {
  id: "step_1_region_understanding",
  title: "任务1：认识研究区",
  objective:
    "了解黄河中下游滩区的空间范围、边界形态、河流走向及周边城镇、农田、水体分布，为后续生态韧性与洪水风险分析建立空间基础。",
  operation:
    "请先观察卫星底图和研究区边界，不急于打开专题图层。重点关注研究区沿黄河分布的空间形态，以及周边城镇、农田、水体与滩区之间的关系。",
  focus: [
    "研究区主要沿什么方向展开？",
    "边界形态是连续分布，还是呈现分段、带状特征？",
    "周边是否有明显的城镇建设区？",
    "农田和水体主要分布在哪些位置？",
    "为什么该区域适合开展生态韧性与洪水风险综合分析？",
  ],
  requirement:
    "请完成一次地图观察，并保存至少1条证据，例如当前视图、点击位置、区域特征描述或智能体提示内容。完成后可进入下一步“选择年份与图层”。",
  thinkingPrompt: "请围绕观察重点形成自己的空间描述，并尝试说明研究区为什么适合开展生态韧性与洪水风险综合分析。",
};

export const yearLayerSelectionTaskCard: TeachingTaskCard = {
  id: "step_2_year_layer_selection",
  title: "任务2：选择年份与图层",
  objective:
    "掌握年份选择与专题图层选择的方法，理解不同年份和不同图层在遥感生态分析中的作用，为后续土地利用变化、植被变化、水体变化、生态韧性和洪水风险分析做准备。",
  operation:
    "请先选择一个分析年份，再选择对应专题图层。建议从2024年开始观察，再切换到2000、2005、2010、2015、2020等年份进行对比。此阶段重点是理解“年份”和“图层”的含义，不急于直接得出结论。",
  layerNotes: [
    "CLCD：用于观察土地利用/覆盖类型；",
    "NDVI：用于观察植被覆盖状况；",
    "EVI：用于补充判断植被生长状态；",
    "水体：用于识别河道、水面和湿地区域；",
    "ER：用于分析生态韧性水平；",
    "FRI：用于分析洪水风险程度。",
  ],
  suggestedActions: [
    "先选择2024年；",
    "打开NDVI或CLCD图层；",
    "观察当前年份的空间分布特征；",
    "再切换到2000年、2010年或2020年；",
    "对比不同年份之间的变化；",
    "尝试理解不同图层代表的生态或风险含义。",
  ],
  focus: [
    "不同年份的同一图层是否存在明显变化？",
    "CLCD和NDVI分别能说明什么问题？",
    "哪些图层更适合分析生态韧性？",
    "哪些图层更适合分析洪水风险？",
    "如果要分析区域变化，应该如何组合年份和图层？",
  ],
  requirement:
    "至少选择1个年份和1个专题图层，并保存当前观察结果作为学习证据。建议记录当前年份、图层名称、观察到的空间分布特征，以及初步判断。",
};

export const lulcVegetationWaterTaskCard: TeachingTaskCard = {
  id: "step_3_lulc_vegetation_water_interpretation",
  title: "任务3：判读土地利用/植被/水体变化",
  objective:
    "通过对比不同年份的土地利用、植被指数和水体分布，识别黄河中下游滩区生态空间变化特征，理解建设用地扩张、植被覆盖变化和水体变化对区域生态环境的影响。",
  operation:
    "请先选择两个或多个年份进行对比，例如2000年与2024年。建议依次查看CLCD、NDVI、EVI和水体图层，观察土地利用类型、植被覆盖程度和水体分布是否发生明显变化。",
  suggestedActions: [
    "打开2000年CLCD图层，观察土地利用格局；",
    "切换到2024年CLCD图层，对比建设用地、耕地、水体等变化；",
    "打开NDVI或EVI图层，观察植被覆盖高值区和低值区；",
    "切换不同年份，判断植被是否增加、减少或发生空间转移；",
    "打开水体图层，观察黄河河道、滩区水面和湿地区域变化；",
    "记录变化明显的区域，并保存为学习证据。",
  ],
  focus: [
    "建设用地是否向滩区或河流附近扩张？",
    "耕地、林地、水体等类型是否发生明显变化？",
    "NDVI/EVI高值区和低值区主要分布在哪里？",
    "水体范围是否存在收缩、扩张或空间转移？",
    "哪些区域的生态空间变化最明显？",
  ],
  requirement:
    "至少完成一次“年份对比 + 图层判读”，并保存1条证据。证据应包括年份、图层名称、观察区域和一句变化描述。",
};

export const erFriAnalysisTaskCard: TeachingTaskCard = {
  id: "step_4_er_fri_analysis",
  title: "任务4：分析生态韧性ER与洪水风险FRI关系",
  objective:
    "理解生态韧性ER与洪水风险FRI之间的空间关系，识别低生态韧性、高洪水风险及二者叠加区域，并尝试结合ERD、ERF等指标解释风险形成原因。",
  operation:
    "请同时查看ER和FRI图层。重点关注生态韧性较低、洪水风险较高的区域，并判断这些区域是否在空间上重叠。随后结合ERD、ERF等指标，分析该区域可能受到建设用地扩张、地形低洼、水体邻近或生态空间破碎等因素影响。",
  suggestedActions: [
    "打开ER图层，观察生态韧性的高值区和低值区；",
    "打开FRI图层，观察洪水风险高值区；",
    "对比ER低值区与FRI高值区是否重叠；",
    "如有“低韧性—高风险识别”按钮，可点击自动识别叠加区域；",
    "打开ERD、ERF等指标图层，分析叠加区域形成原因；",
    "记录一个典型区域，并保存为学习证据。",
  ],
  focus: [
    "哪些区域生态韧性较低？",
    "哪些区域洪水风险较高？",
    "ER低值区与FRI高值区是否存在空间叠加？",
    "叠加区附近是否有建设用地、农田、水体或低洼地形？",
    "ERD、ERF等指标能否解释该区域风险来源？",
  ],
  requirement:
    "至少识别1处“低生态韧性—高洪水风险”叠加区域，并保存证据。证据应包括区域位置、使用图层、观察结果和原因解释。",
};

export const learningReportTaskCard: TeachingTaskCard = {
  id: "step_5_learning_report",
  title: "任务5：生成学习报告",
  objective:
    "整理本次学习过程中使用的研究区域、年份、图层、主要发现、证据截图、统计值、智能体提示和个人结论，形成一份完整的遥感数智学习报告。",
  operation:
    "请回顾前4个步骤的学习过程，检查是否已经完成研究区认识、年份与图层选择、土地利用/植被/水体变化判读，以及ER与FRI关系分析。然后整理证据并生成学习报告。",
  suggestedActions: [
    "研究区域：说明本次分析的区域范围；",
    "分析年份：记录使用的年份，如2000、2010、2020、2024等；",
    "使用图层：列出CLCD、NDVI、EVI、水体、ER、FRI等图层；",
    "主要发现：概括土地利用变化、植被变化、水体变化和风险叠加特征；",
    "证据材料：包括截图、点击位置、统计值、图层名称和智能体提示；",
    "个人结论：用自己的语言总结该区域生态韧性与洪水风险特征；",
    "反思问题：说明后续还可以补充哪些数据或分析。",
  ],
  focus: [
    "研究区域、分析年份和使用图层是否记录清楚？",
    "土地利用、植被、水体、ER与FRI关系的主要发现是否完整？",
    "是否至少整理了1条可支撑结论的学习证据？",
    "统计值、截图、点击位置或智能体提示是否能够支撑个人判断？",
    "个人结论和反思问题是否用自己的语言表达？",
  ],
  requirement: "至少整理1条学习证据，并生成“黄河中下游滩区遥感数智学习报告”。",
};

const teachingTaskCards: Record<string, TeachingTaskCard> = {
  step_1_region_understanding: regionUnderstandingTaskCard,
  step_2_year_layer_selection: yearLayerSelectionTaskCard,
  step_3_lulc_vegetation_water_interpretation: lulcVegetationWaterTaskCard,
  step_4_er_fri_analysis: erFriAnalysisTaskCard,
  step_5_learning_report: learningReportTaskCard,
};

export const activeTeachingTaskCard = computed<TeachingTaskCard | null>(() =>
  activeLearningTaskId.value ? teachingTaskCards[activeLearningTaskId.value] ?? null : null,
);

function resetTeachingTargets() {
  highlightedTeachingTargets.yearSelector = false;
  highlightedTeachingTargets.layerSelector = false;
  highlightedTeachingTargets.layerKeys = [];
  highlightedTeachingTargets.riskIdentification = false;
  highlightedTeachingTargets.evidenceReport = false;
  highlightedTeachingTargets.reportGenerate = false;
  highlightedTeachingTargets.showEvidenceCount = false;
  highlightedTeachingTargets.yearNote = "";
  highlightedTeachingTargets.layerNote = "";
}

function applyStep2TeachingTargets() {
  highlightedTeachingTargets.yearSelector = true;
  highlightedTeachingTargets.layerSelector = true;
  highlightedTeachingTargets.layerKeys = [];
  highlightedTeachingTargets.riskIdentification = false;
  highlightedTeachingTargets.evidenceReport = false;
  highlightedTeachingTargets.reportGenerate = false;
  highlightedTeachingTargets.showEvidenceCount = false;
  highlightedTeachingTargets.yearNote = "可选择：2000、2005、2010、2015、2020、2024。建议先从2024年开始。";
  highlightedTeachingTargets.layerNote = "可选择：CLCD、NDVI、EVI、水体、ER、FRI。建议先打开NDVI或CLCD观察。";
}

function applyStep3TeachingTargets() {
  highlightedTeachingTargets.yearSelector = true;
  highlightedTeachingTargets.layerSelector = true;
  highlightedTeachingTargets.layerKeys = ["clcd", "ndvi", "evi", "water"];
  highlightedTeachingTargets.riskIdentification = false;
  highlightedTeachingTargets.evidenceReport = false;
  highlightedTeachingTargets.reportGenerate = false;
  highlightedTeachingTargets.showEvidenceCount = false;
  highlightedTeachingTargets.yearNote = "建议至少选择两个年份进行对比，例如2000与2024、2010与2024、2020与2024。";
  highlightedTeachingTargets.layerNote = "重点判读：CLCD、NDVI、EVI、水体图层。不要一次性打开所有图层，建议逐个图层对比观察。";
}

function applyStep4TeachingTargets() {
  highlightedTeachingTargets.yearSelector = false;
  highlightedTeachingTargets.layerSelector = true;
  highlightedTeachingTargets.layerKeys = ["four_dim_er", "four_dim_erd", "four_dim_erf", "four_dim_fri"];
  highlightedTeachingTargets.riskIdentification = true;
  highlightedTeachingTargets.evidenceReport = false;
  highlightedTeachingTargets.reportGenerate = false;
  highlightedTeachingTargets.showEvidenceCount = false;
  highlightedTeachingTargets.yearNote = "";
  highlightedTeachingTargets.layerNote = "重点分析：ER、ERD、ERF、FRI。建议同时查看ER与FRI，再结合ERD、ERF解释低韧性—高风险叠加区。";
}

function applyStep5TeachingTargets() {
  highlightedTeachingTargets.yearSelector = false;
  highlightedTeachingTargets.layerSelector = false;
  highlightedTeachingTargets.layerKeys = [];
  highlightedTeachingTargets.riskIdentification = false;
  highlightedTeachingTargets.evidenceReport = true;
  highlightedTeachingTargets.reportGenerate = true;
  highlightedTeachingTargets.showEvidenceCount = true;
  highlightedTeachingTargets.yearNote = "";
  highlightedTeachingTargets.layerNote = "";
}

watch(activeLearningTaskId, (taskId) => {
  if (taskId === "step_2_year_layer_selection") {
    if (taskStatusMap.step_1_region_understanding !== "not_started") {
      taskStatusMap.step_1_region_understanding = "completed";
    }
    taskStatusMap.step_2_year_layer_selection = "in_progress";
    applyStep2TeachingTargets();
    activeRightPanelTab.value = "agent";
  } else if (taskId === "step_3_lulc_vegetation_water_interpretation") {
    if (taskStatusMap.step_2_year_layer_selection !== "not_started") {
      taskStatusMap.step_2_year_layer_selection = "completed";
    }
    taskStatusMap.step_3_lulc_vegetation_water_interpretation = "in_progress";
    applyStep3TeachingTargets();
    activeRightPanelTab.value = "agent";
  } else if (taskId === "step_4_er_fri_analysis") {
    if (taskStatusMap.step_3_lulc_vegetation_water_interpretation !== "not_started") {
      taskStatusMap.step_3_lulc_vegetation_water_interpretation = "completed";
    }
    taskStatusMap.step_4_er_fri_analysis = "in_progress";
    applyStep4TeachingTargets();
    activeRightPanelTab.value = "agent";
  } else if (taskId === "step_5_learning_report") {
    if (taskStatusMap.step_4_er_fri_analysis !== "not_started") {
      taskStatusMap.step_4_er_fri_analysis = "completed";
    }
    taskStatusMap.step_5_learning_report = "in_progress";
    applyStep5TeachingTargets();
    activeRightPanelTab.value = "agent";
  } else {
    resetTeachingTargets();
  }
});

export const teachingPromptLabels: Record<TeachingPromptType, string> = {
  concept_hint: "概念提示",
  method_hint: "方法提示",
  evidence_check: "证据核验",
};

export const teachingPromptQuestions: Record<TeachingPromptType, string> = {
  concept_hint: "请围绕当前学习任务解释关键概念，面向学生提示，不要直接给最终结论。",
  method_hint: "请提示学生下一步应该怎么做，说明应打开哪些图层、比较哪些年份或如何使用点击查询。",
  evidence_check: "请检查当前学习结论是否有足够证据支撑，提醒学生补充图层、年份、区域、统计值、点击位置或截图。",
};

let teachingHintRequestId = 0;
export const pendingTeachingHintRequest = ref<{ id: number; promptType: TeachingPromptType } | null>(null);
export const pendingFloatingTeachingHintRequest = ref<{ id: number; promptType: TeachingPromptType } | null>(null);
export const floatingTeachingHintLoadingPrompt = ref<TeachingPromptType | null>(null);

export function handleTeachingTaskClick(task: TeachingTask) {
  const current = activeLearningTaskId.value;
  if (current && current !== task.id && taskStatusMap[current] === "in_progress") {
    taskStatusMap[current] = "completed";
  }
  activeLearningTaskId.value = task.id;
  taskStatusMap[task.id] = "in_progress";
  activeRightPanelTab.value = "agent";
  if (task.id === "step_1_region_understanding") {
    resetTeachingTargets();
    showOnlyBoundaryMode();
    studyAreaOverviewRequest.value += 1;
    floatingTeachingTipRequest.value += 1;
  } else if (task.id === "step_2_year_layer_selection") {
    if (taskStatusMap.step_1_region_understanding !== "not_started") {
      taskStatusMap.step_1_region_understanding = "completed";
    }
    applyStep2TeachingTargets();
    floatingTeachingTipRequest.value += 1;
  } else if (task.id === "step_3_lulc_vegetation_water_interpretation") {
    if (taskStatusMap.step_2_year_layer_selection !== "not_started") {
      taskStatusMap.step_2_year_layer_selection = "completed";
    }
    applyStep3TeachingTargets();
    floatingTeachingTipRequest.value += 1;
  } else if (task.id === "step_4_er_fri_analysis") {
    if (taskStatusMap.step_3_lulc_vegetation_water_interpretation !== "not_started") {
      taskStatusMap.step_3_lulc_vegetation_water_interpretation = "completed";
    }
    applyStep4TeachingTargets();
    floatingTeachingTipRequest.value += 1;
  } else if (task.id === "step_5_learning_report") {
    if (taskStatusMap.step_4_er_fri_analysis !== "not_started") {
      taskStatusMap.step_4_er_fri_analysis = "completed";
    }
    applyStep5TeachingTargets();
    floatingTeachingTipRequest.value += 1;
  } else {
    resetTeachingTargets();
  }
}

export function requestTeachingHint(promptType: TeachingPromptType) {
  pendingFloatingTeachingHintRequest.value = { id: ++teachingHintRequestId, promptType };
}
