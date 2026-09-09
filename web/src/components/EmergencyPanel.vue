<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { useResilienceStore } from "../stores/resilience";
import { showThematicLayerMode } from "../composables/layerDisplayMode";
import {
  emergencyActive,
  emergencyCatalog,
  emergencyDataset,
  emergencyError,
  emergencyLoading,
  emergencyMapStations,
  emergencyRiskYear,
  loadEmergencyDataset,
  loadEmergencyYear,
  rainfallMode,
  selectEmergencyEvent,
  selectedEmergencyDate,
  selectedEmergencyDay,
  selectedEmergencyYear,
  type EmergencyObservation,
} from "../composables/emergencyState";

const store = useResilienceStore();
const playing = ref(false);
const playbackStart = ref(0);
const playbackEnd = ref(0);
let playbackTimer: number | null = null;

const stationMap = computed(() => new Map((emergencyDataset.value?.stations ?? []).map((station) => [station.id, station])));
const currentEvent = computed(() => emergencyDataset.value?.events.find((event) => event.date === selectedEmergencyDate.value) ?? null);
const observations = computed(() => {
  const field = rainfallMode.value === "rolling3" ? "rolling3" : "rainfall";
  return [...(selectedEmergencyDay.value?.observations ?? [])].sort((a, b) => b[field] - a[field]);
});
const displayPeak = computed(() => rainfallMode.value === "rolling3" ? selectedEmergencyDay.value?.max3Day ?? 0 : selectedEmergencyDay.value?.peak ?? 0);
const playbackIndex = computed(() => Math.max(0, emergencyDataset.value?.days.findIndex((day) => day.date === selectedEmergencyDate.value) ?? 0));
const playbackProgress = computed(() => {
  const span = Math.max(1, (emergencyDataset.value?.days.length ?? 1) - 1);
  return Math.min(100, Math.max(0, (playbackIndex.value / span) * 100));
});
const rainstormCount = computed(() => observations.value.filter((item) => displayValue(item) >= 50).length);
const affectedCount = computed(() => observations.value.filter((item) => displayValue(item) >= 10).length);
const fusionStations = computed(() => [...emergencyMapStations.value].sort((a, b) => b.composite - a.composite));
const highFusionCount = computed(() => fusionStations.value.filter((item) => item.composite >= 55).length);
const responseAssessment = computed(() => {
  const top = fusionStations.value[0];
  const score = top?.composite ?? 0;
  if (score >= 75) return {
    label: "红色响应建议",
    className: "critical",
    detail: `${top.name}联合风险${score}分，建议立即核查沿河低洼点、堤防薄弱段和人员暴露区。`,
  };
  if (score >= 55) return {
    label: "橙色响应建议",
    className: "warning",
    detail: `${top?.name ?? "重点站点"}降水与FRI形成高风险叠加，建议启动重点巡查和部门会商。`,
  };
  if (score >= 35) return {
    label: "黄色关注建议",
    className: "warning",
    detail: "局部出现降水与洪水风险叠加，建议加强站点监测并预置巡查力量。",
  };
  return { label: "常态监测", className: "normal", detail: "当前日期未识别到需要升级响应的降水—洪水复合风险。" };
});

function displayValue(item: EmergencyObservation) {
  return rainfallMode.value === "rolling3" ? item.rolling3 : item.rainfall;
}

function setMode(mode: "daily" | "rolling3") {
  rainfallMode.value = mode;
}

function openRiskLayer(layer: string) {
  store.setYear(emergencyRiskYear.value);
  store.setLayer(layer);
  showThematicLayerMode();
}

async function onYearChange(event: Event) {
  stopPlayback();
  const year = Number((event.target as HTMLSelectElement).value);
  try {
    await loadEmergencyYear(year);
    setPlaybackWindow();
    store.setYear(emergencyRiskYear.value);
  } catch {
    stopPlayback();
  }
}

function onEventChange(event: Event) {
  stopPlayback();
  const date = (event.target as HTMLSelectElement).value;
  selectEmergencyEvent(date);
}

function setPlaybackWindow() {
  const days = emergencyDataset.value?.days ?? [];
  playbackStart.value = 0;
  playbackEnd.value = Math.max(0, days.length - 1);
}

function setDayByIndex(index: number) {
  const days = emergencyDataset.value?.days ?? [];
  const bounded = Math.min(days.length - 1, Math.max(0, index));
  if (days[bounded]) selectedEmergencyDate.value = days[bounded].date;
}

function stopPlayback() {
  playing.value = false;
  if (playbackTimer !== null) window.clearInterval(playbackTimer);
  playbackTimer = null;
}

function startPlayback() {
  stopPlayback();
  playing.value = true;
  if (playbackIndex.value < playbackStart.value || playbackIndex.value >= playbackEnd.value) {
    setDayByIndex(playbackStart.value);
  }
  playbackTimer = window.setInterval(() => {
    const next = playbackIndex.value >= playbackEnd.value ? playbackStart.value : playbackIndex.value + 1;
    setDayByIndex(next);
  }, 820);
}

function togglePlayback() {
  if (playing.value) stopPlayback();
  else startPlayback();
}

function stepDay(offset: number) {
  stopPlayback();
  setDayByIndex(playbackIndex.value + offset);
}

function onTimelineInput(event: Event) {
  stopPlayback();
  setDayByIndex(Number((event.target as HTMLInputElement).value));
}

function onDateInput(event: Event) {
  stopPlayback();
  const date = (event.target as HTMLInputElement).value;
  if (emergencyDataset.value?.days.some((item) => item.date === date)) {
    selectEmergencyEvent(date);
  }
}

onMounted(async () => {
  emergencyActive.value = true;
  store.setLayer("four_dim_fri");
  showThematicLayerMode();
  try {
    await loadEmergencyDataset();
    setPlaybackWindow();
    store.setYear(emergencyRiskYear.value);
  } catch {
    stopPlayback();
  }
});

onBeforeUnmount(() => {
  stopPlayback();
  emergencyActive.value = false;
});
</script>

<template>
  <div class="emergency-panel">
    <section class="emergency-hero">
      <div class="emergency-title-row">
        <span class="emergency-live"><i /> OBSERVED</span>
        <span>实测数据驱动</span>
      </div>
      <h2>降水致灾风险应急研判</h2>
      <p>用国家级气象站观测验证强降水过程，并与洪水风险和生态韧性联动。</p>
    </section>

    <p v-if="emergencyLoading" class="emergency-message">正在读取实测降水记录…</p>
    <p v-else-if="emergencyError" class="emergency-message error">{{ emergencyError }}</p>

    <template v-else-if="emergencyDataset && selectedEmergencyDay">
      <section class="emergency-event-card">
        <div class="emergency-select-grid">
          <div>
            <label for="emergency-year-select">降水年份</label>
            <select id="emergency-year-select" :value="selectedEmergencyYear" @change="onYearChange">
              <option v-for="item in [...(emergencyCatalog?.years ?? [])].reverse()" :key="item.year" :value="item.year">
                {{ item.year }} 年
              </option>
            </select>
          </div>
          <div>
            <label for="emergency-event-select">本年典型强降水过程</label>
            <select id="emergency-event-select" :value="currentEvent?.date ?? ''" @change="onEventChange">
              <option value="" disabled>请选择典型过程</option>
              <option v-for="event in emergencyDataset.events" :key="event.id" :value="event.date">
                {{ event.label }}
              </option>
            </select>
          </div>
        </div>
        <div class="emergency-source-row">
          <span>覆盖 2000—2020 年逐日实测</span>
          <strong>{{ emergencyDataset.metadata.stationCount }} 个沿线站点</strong>
        </div>
      </section>

      <section class="rainfall-timeline">
        <div class="timeline-now">
          <span><i /> 日期由用户选择</span>
          <input
            class="timeline-date-input"
            type="date"
            :min="emergencyDataset.days[0]?.date"
            :max="emergencyDataset.days[emergencyDataset.days.length - 1]?.date"
            :value="selectedEmergencyDate"
            @change="onDateInput"
          />
        </div>
        <input
          type="range"
          min="0"
          :max="emergencyDataset.days.length - 1"
          :value="playbackIndex"
          :style="{ '--timeline-progress': `${playbackProgress}%` }"
          aria-label="降水日期"
          @input="onTimelineInput"
        />
        <div class="timeline-controls">
          <button type="button" aria-label="前一天" @click="stepDay(-1)">‹</button>
          <button type="button" class="timeline-play" @click="togglePlayback">
            {{ playing ? "Ⅱ 暂停" : "▶ 播放" }}
          </button>
          <button type="button" aria-label="后一天" @click="stepDay(1)">›</button>
          <span>{{ emergencyDataset.days[playbackStart]?.date }} — {{ emergencyDataset.days[playbackEnd]?.date }}</span>
        </div>
      </section>

      <div class="rainfall-mode-switch" role="group" aria-label="降水累计时段">
        <button type="button" :class="{ active: rainfallMode === 'daily' }" @click="setMode('daily')">单日降水</button>
        <button type="button" :class="{ active: rainfallMode === 'rolling3' }" @click="setMode('rolling3')">连续3日</button>
      </div>

      <section class="emergency-kpis">
        <article>
          <span>过程峰值</span>
          <strong>{{ displayPeak.toFixed(1) }}</strong>
          <em>mm</em>
        </article>
        <article>
          <span>暴雨站点</span>
          <strong>{{ rainstormCount }}</strong>
          <em>≥50 mm</em>
        </article>
        <article>
          <span>受影响站点</span>
          <strong>{{ affectedCount }}</strong>
          <em>≥10 mm</em>
        </article>
      </section>

      <section class="emergency-concern" :class="responseAssessment.className">
        <div>
          <span>平台辅助响应建议</span>
          <strong>{{ responseAssessment.label }}</strong>
        </div>
        <p>{{ responseAssessment.detail }}</p>
        <small>依据当前日期实测降水与 {{ emergencyRiskYear }} 年 FRI 风险快照联合计算，不等同于政府发布的预警等级。</small>
      </section>

      <section class="emergency-fusion">
        <div class="emergency-section-title"><span>降水 × FRI 联合风险</span><b>{{ emergencyRiskYear }} 风险底图 · {{ highFusionCount }} 个高风险站点</b></div>
        <p class="fusion-formula">降水危险度 ×（0.55 + 0.45 × FRI归一值）</p>
        <div class="fusion-hotspots">
          <article v-for="(item, index) in fusionStations.slice(0, 4)" :key="item.id" :class="`risk-${item.riskLevel}`">
            <span>{{ String(index + 1).padStart(2, '0') }}</span>
            <div><strong>{{ item.name }}</strong><small>{{ item.value.toFixed(1) }} mm · FRI {{ item.fri.toFixed(3) }}</small></div>
            <b>{{ item.composite }}<small>联合分</small></b>
          </article>
        </div>
      </section>

      <section class="emergency-actions">
        <div class="emergency-section-title"><span>应急任务单</span><b>随日期自动更新</b></div>
        <ol>
          <li><b>01</b><span>优先核查 {{ fusionStations.slice(0, 3).map((item) => item.name).join('、') || '沿线站点' }} 周边低洼点和行洪通道。</span></li>
          <li><b>02</b><span>对联合风险 ≥55 分站点启动堤防、涵闸和在建工程巡查，共 {{ highFusionCount }} 处。</span></li>
          <li><b>03</b><span>叠加人口与道路暴露数据，形成转移准备清单和巡查路线。</span></li>
        </ol>
      </section>

      <section class="emergency-linkage">
        <div class="emergency-section-title"><span>风险联动</span><b>点击切换底层模型</b></div>
        <div class="emergency-layer-actions">
          <button type="button" :class="{ active: store.layer === 'four_dim_fri' }" @click="openRiskLayer('four_dim_fri')">FRI 洪水风险</button>
          <button type="button" :class="{ active: store.layer === 'four_dim_erf' }" @click="openRiskLayer('four_dim_erf')">ERF 洪水韧性</button>
          <button type="button" :class="{ active: store.layer === 'four_dim_er' }" @click="openRiskLayer('four_dim_er')">ER 综合韧性</button>
          <button type="button" :class="{ active: store.layer === 'water' }" @click="openRiskLayer('water')">水体频率</button>
        </div>
      </section>

      <section class="emergency-stations">
        <div class="emergency-section-title"><span>站点实测排行</span><b>按雨量排序</b></div>
        <div class="station-risk-list">
          <article v-for="(item, index) in observations.slice(0, 6)" :key="item.stationId">
            <span class="station-rank">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="station-name">
              <strong>{{ stationMap.get(item.stationId)?.name ?? item.stationId }}</strong>
              <small>{{ item.stationId }} · 历史有雨日P{{ item.percentile.toFixed(1) }}</small>
            </span>
            <span class="station-rain">
              <strong>{{ displayValue(item).toFixed(1) }}</strong>
              <small>mm</small>
            </span>
          </article>
        </div>
      </section>

      <section class="emergency-chain">
        <div class="emergency-section-title"><span>应急证据链</span><b>实测 → 风险 → 处置</b></div>
        <div class="evidence-chain-flow">
          <span><b>01</b>站点实测</span>
          <span><b>02</b>极端判别</span>
          <span><b>03</b>风险叠加</span>
          <span><b>04</b>会商输出</span>
        </div>
      </section>

      <p class="emergency-limitation">{{ emergencyDataset.metadata.limitation }}</p>
    </template>
  </div>
</template>
