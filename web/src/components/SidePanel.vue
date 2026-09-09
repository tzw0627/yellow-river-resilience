<script setup lang="ts">
import YearSelector from "./YearSelector.vue";
import LayerTree from "./LayerTree.vue";
import RegionSelector from "./RegionSelector.vue";
import { highlightedTeachingTargets } from "../composables/teachingState";
</script>

<template>
  <aside class="side-panel">
    <div class="brand-block">
      <div class="workbench-heading">
        <span class="workbench-mark">YR</span>
        <span>
          <small>RESILIENCE WORKBENCH</small>
          <h2>韧性研判工作台</h2>
        </span>
      </div>
      <p>从多源遥感到治理证据，定位低韧性与高风险重叠区。</p>
      <div class="workflow-rail" aria-label="研判流程">
        <span><b>01</b>选时</span>
        <span><b>02</b>选层</span>
        <span><b>03</b>研判</span>
        <span><b>04</b>取证</span>
      </div>
    </div>

    <div class="control-group teaching-target-block" :class="{ 'teaching-target-highlight': highlightedTeachingTargets.yearSelector }">
      <div class="group-title"><span>01</span> 时序基线</div>
      <YearSelector />
      <p v-if="highlightedTeachingTargets.yearSelector" class="teaching-target-note">
        {{ highlightedTeachingTargets.yearNote }}
      </p>
    </div>

    <div class="control-group">
      <div class="group-title"><span>02</span> 管理单元</div>
      <RegionSelector />
    </div>

    <div class="control-group teaching-target-block" :class="{ 'teaching-target-highlight': highlightedTeachingTargets.layerSelector }">
      <div class="group-title"><span>03</span> 数据与模型图层</div>
      <LayerTree />
      <p v-if="highlightedTeachingTargets.layerSelector" class="teaching-target-note">
        {{ highlightedTeachingTargets.layerNote }}
      </p>
    </div>
  </aside>
</template>
