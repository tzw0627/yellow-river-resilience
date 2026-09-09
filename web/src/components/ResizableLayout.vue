<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from "vue";

const LEFT_STORAGE_KEY = "yellow-river-layout-left-width";
const RIGHT_STORAGE_KEY = "yellow-river-layout-right-width";

const LEFT_MIN = 220;
const LEFT_MAX = 460;
const RIGHT_MIN = 280;
const RIGHT_MAX = 520;
const CENTER_MIN = 600;

type DragSide = "left" | "right";

interface DragState {
  side: DragSide;
  startX: number;
  startLeft: number;
  startRight: number;
}

const layout = ref<HTMLElement | null>(null);
const leftHandle = ref<HTMLElement | null>(null);
const rightHandle = ref<HTMLElement | null>(null);
const leftWidth = ref(readStoredWidth(LEFT_STORAGE_KEY, 300, LEFT_MIN, LEFT_MAX));
const rightWidth = ref(readStoredWidth(RIGHT_STORAGE_KEY, 320, RIGHT_MIN, RIGHT_MAX));
const dragState = ref<DragState | null>(null);

const leftStyle = computed(() => ({
  width: `${leftWidth.value}px`,
}));

const rightStyle = computed(() => ({
  width: `${rightWidth.value}px`,
}));

const layoutStyle = computed(() => ({
  "--left-panel-width": `${leftWidth.value}px`,
  "--right-panel-width": `${rightWidth.value}px`,
}));

function readStoredWidth(key: string, fallback: number, min: number, max: number) {
  const value = Number(window.localStorage.getItem(key));
  return Number.isFinite(value) ? clamp(value, min, max) : fallback;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

function availableWidth() {
  const total = layout.value?.clientWidth ?? 0;
  const handles = (leftHandle.value?.offsetWidth ?? 0) + (rightHandle.value?.offsetWidth ?? 0);
  return Math.max(0, total - handles);
}

function widthsForCenterMinimum(nextLeft: number, nextRight: number, priority?: DragSide) {
  let left = clamp(nextLeft, LEFT_MIN, LEFT_MAX);
  let right = clamp(nextRight, RIGHT_MIN, RIGHT_MAX);
  let overflow = left + right + CENTER_MIN - availableWidth();

  if (overflow <= 0) return { left, right };

  if (priority === "left") {
    const reduceLeft = Math.min(overflow, Math.max(0, left - LEFT_MIN));
    left -= reduceLeft;
    overflow -= reduceLeft;
  } else if (priority === "right") {
    const reduceRight = Math.min(overflow, Math.max(0, right - RIGHT_MIN));
    right -= reduceRight;
    overflow -= reduceRight;
  }

  if (overflow > 0) {
    const reduceRight = Math.min(overflow, Math.max(0, right - RIGHT_MIN));
    right -= reduceRight;
    overflow -= reduceRight;
  }

  if (overflow > 0) {
    const reduceLeft = Math.min(overflow, Math.max(0, left - LEFT_MIN));
    left -= reduceLeft;
  }

  return { left, right };
}

function applyWidths(nextLeft: number, nextRight: number, priority?: DragSide) {
  const widths = widthsForCenterMinimum(nextLeft, nextRight, priority);
  leftWidth.value = widths.left;
  rightWidth.value = widths.right;
}

function startDrag(side: DragSide, event: PointerEvent) {
  event.preventDefault();
  dragState.value = {
    side,
    startX: event.clientX,
    startLeft: leftWidth.value,
    startRight: rightWidth.value,
  };
  document.body.classList.add("is-resizing-layout");
  window.addEventListener("pointermove", onPointerMove);
  window.addEventListener("pointerup", stopDrag);
  window.addEventListener("pointercancel", stopDrag);
}

function onPointerMove(event: PointerEvent) {
  const state = dragState.value;
  if (!state) return;

  const deltaX = event.clientX - state.startX;
  if (state.side === "left") {
    applyWidths(state.startLeft + deltaX, state.startRight, "left");
  } else {
    applyWidths(state.startLeft, state.startRight - deltaX, "right");
  }
}

function stopDrag() {
  if (!dragState.value) return;
  dragState.value = null;
  document.body.classList.remove("is-resizing-layout");
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", stopDrag);
  window.removeEventListener("pointercancel", stopDrag);
  saveWidths();
  requestAnimationFrame(() => {
    window.dispatchEvent(new Event("resize"));
  });
}

function saveWidths() {
  window.localStorage.setItem(LEFT_STORAGE_KEY, String(Math.round(leftWidth.value)));
  window.localStorage.setItem(RIGHT_STORAGE_KEY, String(Math.round(rightWidth.value)));
}

function reconcileWidths() {
  applyWidths(leftWidth.value, rightWidth.value);
}

onMounted(async () => {
  await nextTick();
  reconcileWidths();
  window.addEventListener("resize", reconcileWidths);
});

onBeforeUnmount(() => {
  document.body.classList.remove("is-resizing-layout");
  window.removeEventListener("resize", reconcileWidths);
  window.removeEventListener("pointermove", onPointerMove);
  window.removeEventListener("pointerup", stopDrag);
  window.removeEventListener("pointercancel", stopDrag);
});
</script>

<template>
  <div ref="layout" class="resizable-workspace" :class="{ resizing: dragState }" :style="layoutStyle">
    <div class="resizable-panel resizable-panel-left" :style="leftStyle">
      <slot name="left" />
    </div>

    <button
      ref="leftHandle"
      class="resize-handle resize-handle-left"
      type="button"
      aria-label="拖拽调整左侧面板宽度"
      @pointerdown="startDrag('left', $event)"
    />

    <div class="resizable-center">
      <slot name="center" />
    </div>

    <button
      ref="rightHandle"
      class="resize-handle resize-handle-right"
      type="button"
      aria-label="拖拽调整右侧面板宽度"
      @pointerdown="startDrag('right', $event)"
    />

    <div class="resizable-panel resizable-panel-right" :style="rightStyle">
      <slot name="right" />
    </div>
  </div>
</template>
