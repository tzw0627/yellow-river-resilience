<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import { useResilienceStore } from "../stores/resilience";
import { chatStream, type ChatPayload } from "../services/api";
import { useAgentProvider } from "../composables/agentProvider";
import {
  activeLearningTaskId,
  activeTeachingTask,
  activeTeachingTaskCard,
  type TeachingPromptType,
} from "../composables/teachingState";
import type { ChatMessage } from "../config/types";

marked.setOptions({ breaks: true, gfm: true });

function renderMarkdown(text: string): string {
  const html = marked.parse(text, { async: false }) as string;
  return DOMPurify.sanitize(html);
}

const store = useResilienceStore();
const {
  status,
  selectedProvider,
  providerOptions,
  selectedProviderConfigured,
  selectedProviderModel,
  loadAgentProviderStatus,
  selectProvider,
} = useAgentProvider();
const input = ref("");
const sending = ref(false);
const messages = ref<ChatMessage[]>([
  {
    role: "assistant",
    content: "你好，我是黄河滩区生态韧性分析助手。请选择教学任务、区域案例或图层后，我会结合当前上下文提供引导。",
  },
]);

const taskLabel = computed(() => activeTeachingTask.value?.title ?? "未选择");

const contextItems = computed(() => [
  { label: "年份", value: `${store.year}` },
  { label: "图层", value: store.selectedLayerMeta?.label ?? store.layer.toUpperCase() },
  { label: "学习任务", value: taskLabel.value },
]);

function buildPayload(chatMessages: ChatMessage[], promptType?: TeachingPromptType): ChatPayload {
  const stat = store.timelineStat(store.year, store.layer);
  const region = store.selectedRegionId ? store.selectedRegion : null;
  const task = activeTeachingTask.value;
  return {
    messages: chatMessages,
    provider: selectedProvider.value,
    year: store.year,
    layer: store.layer,
    regionId: store.selectedRegionId || undefined,
    query: store.query,
    mode: promptType ? "teaching" : store.serviceScenario || undefined,
    learning_task_id: activeLearningTaskId.value || undefined,
    prompt_type: promptType,
    layer_summary: stat ? { ...stat } : null,
    teaching_context: {
      mode: promptType ? "teaching" : store.serviceScenario || null,
      learning_task_id: activeLearningTaskId.value,
      learning_task_title: task?.title ?? "未选择",
      learning_task_prompt: task?.prompt ?? "",
      prompt_type: promptType,
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
      layer_summary: stat ? { ...stat } : null,
    },
  };
}

onMounted(async () => {
  await loadAgentProviderStatus();
});

async function send() {
  const text = input.value.trim();
  if (!text || sending.value) return;
  input.value = "";
  messages.value.push({ role: "user", content: text });
  const assistant: ChatMessage = { role: "assistant", content: "" };
  messages.value.push(assistant);
  sending.value = true;
  try {
    await chatStream(
      buildPayload(messages.value.filter((m) => m.role !== "assistant" || m.content)),
      (delta) => {
        assistant.content += delta;
      },
    );
  } catch (err) {
    assistant.content = `调用失败：${err instanceof Error ? err.message : String(err)}`;
  } finally {
    sending.value = false;
  }
}

</script>

<template>
  <div class="agent-card">
    <div class="group-title">大模型智能体</div>
    <div class="agent-model-switcher">
      <div class="agent-model-buttons">
        <button
          v-for="provider in providerOptions"
          :key="provider.id"
          type="button"
          :class="['agent-model-button', { active: selectedProvider === provider.id }]"
          @click="selectProvider(provider.id)"
        >
          {{ provider.id === "openai" ? "GPT-4o-mini" : "Xiaomi MiMo-V2.5" }}
        </button>
      </div>
    </div>
    <div v-if="status" :class="['agent-status', selectedProviderConfigured ? 'on' : 'off']">
      {{ selectedProviderConfigured ? `已接入：${selectedProviderModel}` : "当前提供商未配置 API Key（使用规则降级回答）" }}
      <span v-if="status.rag">；RAG 已索引 {{ status.rag.documents }} 条数据文档</span>
    </div>
    <div v-else class="agent-status off">后端未连接，请先启动 FastAPI（端口 8000）。</div>

    <section class="agent-context-card">
      <div class="agent-context-title">当前上下文</div>
      <div class="agent-context-grid">
        <span v-for="item in contextItems" :key="item.label">
          <em>{{ item.label }}</em>
          <strong>{{ item.value }}</strong>
        </span>
      </div>
    </section>

    <section v-if="activeTeachingTaskCard" class="learning-task-card">
      <div class="learning-task-card-title">{{ activeTeachingTaskCard.title }}</div>
      <div class="learning-task-section">
        <strong>学习目标</strong>
        <p>{{ activeTeachingTaskCard.objective }}</p>
      </div>
      <div class="learning-task-section">
        <strong>操作提示</strong>
        <p>{{ activeTeachingTaskCard.operation }}</p>
      </div>
      <div v-if="activeTeachingTaskCard.layerNotes?.length" class="learning-task-section">
        <strong>图层说明</strong>
        <ul class="learning-layer-note-list">
          <li v-for="item in activeTeachingTaskCard.layerNotes" :key="item">{{ item }}</li>
        </ul>
      </div>
      <div v-if="activeTeachingTaskCard.suggestedActions?.length" class="learning-task-section">
        <strong>建议操作</strong>
        <ol>
          <li v-for="item in activeTeachingTaskCard.suggestedActions" :key="item">{{ item }}</li>
        </ol>
      </div>
      <div class="learning-task-section">
        <strong>{{ activeTeachingTaskCard.layerNotes?.length ? "思考问题" : "观察重点" }}</strong>
        <ul>
          <li v-for="item in activeTeachingTaskCard.focus" :key="item">{{ item }}</li>
        </ul>
      </div>
      <div v-if="activeTeachingTaskCard.thinkingPrompt" class="learning-task-section">
        <strong>思考问题</strong>
        <p>{{ activeTeachingTaskCard.thinkingPrompt }}</p>
      </div>
      <div class="learning-task-section">
        <strong>完成要求</strong>
        <p>{{ activeTeachingTaskCard.requirement }}</p>
      </div>
    </section>

    <div class="chat-log">
      <div v-for="(m, i) in messages" :key="i" :class="['chat-msg', m.role]">
        <span v-if="m.role !== 'assistant'">{{ m.content }}</span>
        <div v-else-if="m.content" class="md" v-html="renderMarkdown(m.content)" />
        <span v-else-if="sending && i === messages.length - 1">思考中...</span>
      </div>
    </div>

    <div class="chat-input-row">
      <textarea
        v-model="input"
        placeholder="例如：2024 年 NDVI 中位数是多少？洪水风险高的区域有什么建议？"
        @keydown.enter.exact.prevent="send"
      />
      <button class="btn" :disabled="sending" @click="send">发送</button>
    </div>
  </div>
</template>
