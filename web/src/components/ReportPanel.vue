<script setup lang="ts">
import { computed, ref } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { downloadReport } from "../services/api";
import { learningEvidenceItems } from "../composables/teachingState";

const store = useResilienceStore();

const format = ref<"docx" | "pdf">("docx");
const title = ref("黄河中下游滩区生态韧性与洪水风险研判报告");
const busy = ref(false);
const message = ref("");

const candidateLayers = computed(() =>
  (store.summary?.layers ?? []).filter((l) => store.timelineStat(store.year, l.id)),
);

const selected = ref<string[]>([]);
const reportSuggestions = [
  "研判范围与时间",
  "实测降水过程",
  "洪水风险与韧性短板",
  "重点区域和站点",
  "处置建议",
  "数据来源与适用边界",
];

function ensureDefault() {
  if (selected.value.length === 0) {
    selected.value = candidateLayers.value.slice(0, 4).map((l) => l.id);
  }
}
ensureDefault();

async function generate() {
  if (selected.value.length === 0) {
    message.value = "请至少选择一个图层。";
    return;
  }
  busy.value = true;
  message.value = "";
  try {
    await downloadReport({
      year: store.year,
      layers: selected.value,
      title: title.value,
      format: format.value,
      evidence: learningEvidenceItems.value,
    });
    message.value = "报告已生成，可下载查看。";
  } catch (err) {
    message.value = `生成失败：${err instanceof Error ? err.message : String(err)}`;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="report-card">
    <div class="group-title">报告生成（{{ store.year }} 年）</div>

    <section class="report-section">
      <label class="report-field">
        <span>报告标题</span>
        <input v-model="title" />
      </label>
    </section>

    <section class="report-section report-guidance-section">
      <div class="report-section-title">报告内容建议</div>
      <ol class="report-suggestion-list">
        <li v-for="item in reportSuggestions" :key="item">{{ item }}</li>
      </ol>
    </section>

    <section class="report-section report-evidence-section">
      <div class="report-section-title">研判证据</div>
      <div class="report-evidence-count">
        <span>当前证据</span>
        <strong>{{ learningEvidenceItems.length }} 条</strong>
      </div>
      <p v-if="learningEvidenceItems.length === 0" class="empty-evidence-tip">
        当前未保存地图点查证据，可直接生成基础研判报告。
      </p>
      <div v-else class="report-evidence-list">
        <article v-for="(item, index) in learningEvidenceItems.slice(0, 5)" :key="item.id">
          <strong>证据 {{ learningEvidenceItems.length - index }}｜{{ item.taskTitle }}</strong>
          <span>{{ item.year }} 年 · {{ item.layer }} · {{ item.region }}</span>
        </article>
      </div>
    </section>

    <section class="report-section">
      <div class="report-section-title">导出格式</div>
      <div class="report-choice-row">
        <label><input type="radio" value="docx" v-model="format" /> Word</label>
        <label><input type="radio" value="pdf" v-model="format" /> PDF</label>
      </div>
    </section>

    <section class="report-section">
      <div class="report-section-title">选择图层</div>
      <div class="report-layers">
        <label v-for="l in candidateLayers" :key="l.id">
          <input type="checkbox" :value="l.id" v-model="selected" />
          {{ l.label }}
        </label>
      </div>
      <p v-if="candidateLayers.length === 0" class="layer-description">该年份暂无可用统计图层。</p>
    </section>

    <section class="report-actions">
      <button class="btn report-submit" :disabled="busy" @click="generate">{{ busy ? "生成中..." : "生成并下载" }}</button>
      <span v-if="message" class="report-message" :class="{ success: message.includes('已生成') }">{{ message }}</span>
    </section>
  </div>
</template>
