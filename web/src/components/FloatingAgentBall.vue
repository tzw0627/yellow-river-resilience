<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { chat, type ChatPayload } from "../services/api";
import { useAgentProvider } from "../composables/agentProvider";
import {
  activeLearningTaskId,
  activeTeachingTask,
  floatingTeachingHintLoadingPrompt,
  floatingTeachingTipRequest,
  floatingTeachingTips,
  learningEvidenceItems,
  pendingFloatingTeachingHintRequest,
  teachingPromptLabels,
  teachingPromptQuestions,
  type TeachingPromptType,
} from "../composables/teachingState";
import type { ChatMessage } from "../config/types";

const BALL_SIZE = 70;
const PANEL_WIDTH = 330;
const PANEL_HEIGHT = 420;
const PANEL_GAP = 14;
const EDGE_PADDING = 12;
const TEACHING_TIP_DURATION = 7000;
const STORAGE_KEY = "yr-floating-agent-ball-position";

const store = useResilienceStore();
const {
  selectedProvider,
  providerOptions,
  selectedProviderConfigured,
  selectedProviderModel,
  loadAgentProviderStatus,
  selectProvider,
} = useAgentProvider();
const layerRoot = ref<HTMLElement | null>(null);
const input = ref("");
const isOpen = ref(false);
const isDragging = ref(false);
const hasMoved = ref(false);
const loading = ref(false);
const floatingTeachingTip = ref("");
const showFloatingTeachingTip = ref(false);
let teachingTipTimer: ReturnType<typeof window.setTimeout> | null = null;
const position = ref({ x: 0, y: 0 });
const dragStart = { pointerX: 0, pointerY: 0, x: 0, y: 0 };
const messages = ref<ChatMessage[]>([]);
const handledFloatingTeachingHintId = ref(0);
const activeFloatingHintLabel = ref("");

const activeTaskTitle = computed(() => activeTeachingTask.value?.title ?? "未选择");

const currentMode = computed(() => (store.serviceScenario === "teaching" ? "teaching" : store.serviceScenario));

const panelStyle = computed(() => {
  const area = safeArea();
  const openLeft = position.value.x + BALL_SIZE + PANEL_GAP + PANEL_WIDTH > area.maxX;
  const rawX = openLeft ? position.value.x - PANEL_WIDTH - PANEL_GAP : position.value.x + BALL_SIZE + PANEL_GAP;
  const rawY = position.value.y - 126;
  return {
    left: `${clamp(rawX, area.minX, Math.max(area.minX, area.maxX + BALL_SIZE - PANEL_WIDTH))}px`,
    top: `${clamp(rawY, area.minY, Math.max(area.minY, area.maxY + BALL_SIZE - PANEL_HEIGHT))}px`,
  };
});

const teachingTipStyle = computed(() => {
  const area = safeArea();
  const tipWidth = 330;
  const tipHeight = 140;
  const canShowAbove = position.value.y - tipHeight - PANEL_GAP >= area.minY;
  const rawX = position.value.x + BALL_SIZE / 2 - tipWidth / 2;
  const rawY = canShowAbove ? position.value.y - tipHeight - PANEL_GAP : position.value.y + BALL_SIZE + PANEL_GAP;
  return {
    left: `${clamp(rawX, area.minX, Math.max(area.minX, area.maxX + BALL_SIZE - tipWidth))}px`,
    top: `${clamp(rawY, area.minY, Math.max(area.minY, area.maxY + BALL_SIZE - tipHeight))}px`,
  };
});

function clamp(value: number, min: number, max: number) {
  return Math.min(Math.max(value, min), max);
}

function viewportBounds() {
  const rect = layerRoot.value?.getBoundingClientRect();
  return {
    width: rect?.width ?? 0,
    height: rect?.height ?? 0,
  };
}

function readCssPixel(style: CSSStyleDeclaration, name: string, fallback: number) {
  const value = Number.parseFloat(style.getPropertyValue(name));
  return Number.isFinite(value) ? value : fallback;
}

function safeArea() {
  const bounds = viewportBounds();
  const workspace = layerRoot.value?.closest(".resizable-workspace");
  const style = workspace ? getComputedStyle(workspace) : null;
  const leftPanel = style ? readCssPixel(style, "--left-panel-width", 300) : 300;
  const rightPanel = style ? readCssPixel(style, "--right-panel-width", 320) : 320;
  const gap = style ? readCssPixel(style, "--overlay-gap", 14) : 14;
  const sidePadding = gap + 22;
  const topPadding = gap + 18;
  const bottomPadding = gap + 22;

  return {
    minX: leftPanel + sidePadding,
    maxX: Math.max(leftPanel + sidePadding, bounds.width - rightPanel - sidePadding - BALL_SIZE),
    minY: topPadding,
    maxY: Math.max(topPadding, bounds.height - bottomPadding - BALL_SIZE),
    width: bounds.width,
    height: bounds.height,
  };
}

function constrain(next: { x: number; y: number }) {
  const area = safeArea();
  return {
    x: clamp(next.x, area.minX, area.maxX),
    y: clamp(next.y, area.minY, area.maxY),
  };
}

function savePosition() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(position.value));
}

function restorePosition() {
  const area = safeArea();
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved) {
    try {
      const parsed = JSON.parse(saved) as { x?: number; y?: number };
      if (typeof parsed.x === "number" && typeof parsed.y === "number") {
        position.value = constrain({ x: parsed.x, y: parsed.y });
        return;
      }
    } catch {
      localStorage.removeItem(STORAGE_KEY);
    }
  }
  position.value = constrain({
    x: area.maxX - 28,
    y: Math.max(area.minY, area.height * 0.58),
  });
}

function onPointerDown(event: PointerEvent) {
  if (event.button !== 0) return;
  event.preventDefault();
  event.stopPropagation();
  isDragging.value = true;
  hasMoved.value = false;
  dragStart.pointerX = event.clientX;
  dragStart.pointerY = event.clientY;
  dragStart.x = position.value.x;
  dragStart.y = position.value.y;
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", onPointerUp, { once: true });
}

function onPointerMove(event: PointerEvent) {
  if (!isDragging.value) return;
  const dx = event.clientX - dragStart.pointerX;
  const dy = event.clientY - dragStart.pointerY;
  if (Math.abs(dx) + Math.abs(dy) > 5) hasMoved.value = true;
  position.value = constrain({ x: dragStart.x + dx, y: dragStart.y + dy });
}

function onPointerUp() {
  if (!isDragging.value) return;
  isDragging.value = false;
  window.removeEventListener("pointermove", onPointerMove);
  savePosition();
  if (!hasMoved.value) isOpen.value = !isOpen.value;
}

function closePanel() {
  isOpen.value = false;
}

function hideFloatingTeachingTip() {
  showFloatingTeachingTip.value = false;
  if (teachingTipTimer) {
    window.clearTimeout(teachingTipTimer);
    teachingTipTimer = null;
  }
}

function triggerFloatingTeachingTip(taskId = activeLearningTaskId.value) {
  if (!taskId) return;
  const tip = floatingTeachingTips[taskId];
  if (!tip) return;
  floatingTeachingTip.value = tip;
  showFloatingTeachingTip.value = true;
  if (teachingTipTimer) window.clearTimeout(teachingTipTimer);
  teachingTipTimer = window.setTimeout(() => {
    showFloatingTeachingTip.value = false;
    teachingTipTimer = null;
  }, TEACHING_TIP_DURATION);
}

watch(activeLearningTaskId, (taskId) => {
  activeFloatingHintLabel.value = "";
  hideFloatingTeachingTip();
  if (taskId) triggerFloatingTeachingTip(taskId);
});

watch(floatingTeachingTipRequest, (requestId) => {
  if (requestId > 0) triggerFloatingTeachingTip();
});

function buildPayload(chatMessages: ChatMessage[], promptType?: TeachingPromptType): ChatPayload {
  const stat = store.timelineStat(store.year, store.layer);
  const layerSummary = stat ? { ...stat } : null;
  const task = activeTeachingTask.value;
  const region = store.selectedRegionId ? store.selectedRegion : null;
  return {
    messages: chatMessages,
    provider: selectedProvider.value,
    year: store.year,
    layer: store.layer,
    regionId: store.selectedRegionId || undefined,
    mode: promptType ? "teaching" : currentMode.value || undefined,
    learning_task_id: activeLearningTaskId.value || undefined,
    prompt_type: promptType,
    source: "floating_agent_ball",
    query: store.query,
    layer_summary: layerSummary,
    teaching_context: {
      source: "floating_agent_ball",
      mode: promptType ? "teaching" : currentMode.value || null,
      learning_task_id: activeLearningTaskId.value,
      learning_task_title: task?.title ?? "未选择",
      learning_task_prompt: task?.prompt ?? "",
      prompt_type: promptType,
      evidence_count: learningEvidenceItems.value.length,
      year: store.year,
      region_id: store.selectedRegionId || null,
      region: region
        ? {
            city: region.city,
            name: region.name,
            adminCode: region.adminCode,
          }
        : null,
      layer_id: store.layer,
      layer_label: store.selectedLayerMeta?.label ?? store.layer,
      query: store.query,
      layer_summary: layerSummary,
    },
  };
}

async function send() {
  const text = input.value.trim();
  if (!text || loading.value) return;
  input.value = "";
  messages.value.push({ role: "user", content: text });
  const assistant: ChatMessage = { role: "assistant", content: "" };
  messages.value.push(assistant);
  loading.value = true;
  try {
    const result = await chat(buildPayload(messages.value.filter((message) => message.content)));
    assistant.content = result.reply;
  } catch {
    assistant.content = "智能体暂时无法回答，请稍后重试。";
  } finally {
    loading.value = false;
  }
}

function teachingHintPrompt(promptType: TeachingPromptType) {
  const label = teachingPromptLabels[promptType];
  const task = activeTeachingTask.value;
  const taskText = task ? `当前学习任务：${task.title}。${task.prompt}` : "当前学习任务：未选择。";
  return `【${label}】当前年份：${store.year}；当前图层：${store.selectedLayerMeta?.label ?? store.layer}；${taskText}${teachingPromptQuestions[promptType]}请面向学生进行即时教学引导，不要直接替学生完成最终结论。`;
}

async function handleFloatingTeachingHint(promptType: TeachingPromptType) {
  const label = teachingPromptLabels[promptType];
  activeFloatingHintLabel.value = `【${label}】`;
  isOpen.value = true;
  hideFloatingTeachingTip();

  if (!activeLearningTaskId.value) {
    messages.value.push({
      role: "assistant",
      content: `【${label}】\n\n请先选择一个教学任务，再获取更有针对性的AI助教提示。`,
    });
    return;
  }

  const assistant: ChatMessage = {
    role: "assistant",
    content: `【${label}】\n\n当前年份：${store.year}；当前图层：${store.selectedLayerMeta?.label ?? store.layer}；当前学习任务：${activeTaskTitle.value}。\n\n`,
  };
  messages.value.push(assistant);
  loading.value = true;
  floatingTeachingHintLoadingPrompt.value = promptType;
  try {
    const result = await chat(buildPayload([{ role: "user", content: teachingHintPrompt(promptType) }], promptType));
    assistant.content += result.reply;
  } catch {
    assistant.content += "AI助教暂时无法响应，请稍后重试。";
  } finally {
    loading.value = false;
    floatingTeachingHintLoadingPrompt.value = null;
  }
}

watch(
  pendingFloatingTeachingHintRequest,
  (request) => {
    if (!request || request.id === handledFloatingTeachingHintId.value) return;
    handledFloatingTeachingHintId.value = request.id;
    void handleFloatingTeachingHint(request.promptType);
  },
  { immediate: true },
);

function onResize() {
  position.value = constrain(position.value);
  savePosition();
}

onMounted(async () => {
  await nextTick();
  await loadAgentProviderStatus();
  restorePosition();
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  window.removeEventListener("pointermove", onPointerMove);
  hideFloatingTeachingTip();
});
</script>

<template>
  <div ref="layerRoot" class="floating-agent-layer" aria-label="地图智能体助手">
    <button
      class="floating-agent-ball"
      :class="{ dragging: isDragging, active: isOpen }"
      :style="{ left: `${position.x}px`, top: `${position.y}px` }"
      type="button"
      title="智能体助手"
      @pointerdown="onPointerDown"
    >
      <span class="agent-aura" aria-hidden="true"></span>
      <span class="robot-antenna antenna-left" aria-hidden="true"></span>
      <span class="robot-antenna antenna-right" aria-hidden="true"></span>
      <span class="robot-ear ear-left" aria-hidden="true"></span>
      <span class="robot-ear ear-right" aria-hidden="true"></span>
      <span class="robot-head" aria-hidden="true">
        <span class="robot-plate plate-left"></span>
        <span class="robot-plate plate-right"></span>
        <span class="robot-ai-badge">AI</span>
        <span class="robot-face">
          <span class="robot-eye eye-left"></span>
          <span class="robot-eye eye-right"></span>
          <span class="robot-face-shine"></span>
        </span>
      </span>
    </button>

    <aside
      v-if="showFloatingTeachingTip && !isOpen"
      class="floating-teaching-tip"
      :style="teachingTipStyle"
      aria-live="polite"
    >
      {{ floatingTeachingTip }}
    </aside>

    <section v-if="isOpen" class="floating-agent-panel" :style="panelStyle" @pointerdown.stop>
      <div class="floating-agent-panel-head">
        <strong>智能体助手</strong>
        <span v-if="activeFloatingHintLabel" class="floating-agent-hint-label">{{ activeFloatingHintLabel }}</span>
        <button type="button" class="floating-agent-close" title="收起" @click="closePanel">×</button>
      </div>
      <div v-if="showFloatingTeachingTip" class="floating-agent-panel-tip" aria-live="polite">
        {{ floatingTeachingTip }}
      </div>
      <p class="floating-agent-welcome">
        你好，我是黄河滩区生态韧性分析助手。可以问我图层的数值、多年变化或治理建议。
      </p>

      <div class="floating-agent-models">
        <div class="floating-agent-model-buttons">
          <button
            v-for="provider in providerOptions"
            :key="provider.id"
            type="button"
            :class="['floating-agent-model-button', { active: selectedProvider === provider.id }]"
            @click="selectProvider(provider.id)"
          >
            {{ provider.id === "openai" ? "GPT" : "MiMo" }}
          </button>
        </div>
        <span :class="['floating-agent-model-status', selectedProviderConfigured ? 'on' : 'off']">
          {{ selectedProviderModel }} · {{ selectedProviderConfigured ? "已连接" : "未配置" }}
        </span>
      </div>

      <div class="floating-agent-context">
        <span>年份：{{ store.year }}</span>
        <span>图层：{{ store.selectedLayerMeta?.label ?? store.layer }}</span>
        <span>任务：{{ activeTaskTitle }}</span>
      </div>

      <div class="floating-agent-messages">
        <div v-for="(message, index) in messages" :key="index" :class="['floating-agent-msg', message.role]">
          {{ message.content || (loading && index === messages.length - 1 ? "思考中..." : "") }}
        </div>
      </div>

      <div class="floating-agent-input-row">
        <input
          v-model="input"
          placeholder="例如：2024年NDVI中位数是多少？洪水风险高的区域主要在哪？"
          @keydown.enter.prevent="send"
        />
        <button type="button" :disabled="loading" @click="send">{{ loading ? "思考中..." : "发送" }}</button>
      </div>
    </section>
  </div>
</template>
