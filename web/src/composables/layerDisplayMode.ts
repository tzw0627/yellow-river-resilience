import { ref } from "vue";

export const boundaryOnlyMode = ref(false);
export const studyAreaBoundaryVisible = ref(true);

export function showOnlyBoundaryMode() {
  boundaryOnlyMode.value = true;
  studyAreaBoundaryVisible.value = true;
}

export function showThematicLayerMode() {
  boundaryOnlyMode.value = false;
  studyAreaBoundaryVisible.value = true;
}

export function toggleStudyAreaBoundary() {
  studyAreaBoundaryVisible.value = !studyAreaBoundaryVisible.value;
}
