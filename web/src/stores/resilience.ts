import { defineStore } from "pinia";
import {
  CATEGORICAL_LAYERS,
  CASE_LAYERS,
  DEFAULT_REGION_CASE,
  FOUR_DIM_YEARS,
  currentYearAvailabilityRaw,
  regionCasesFromBoundary,
  realDataConfig,
  realDataYearEntry,
  spatialBounds,
  supplementalLayerStats,
} from "../config";
import type { RegionAnalysis, RegionAnalysisFile, RegionBoundaryCollection, RegionCase, ServiceScenario } from "../config";
import type { Bounds, LayerMeta, LayerStat, LayerSummary, QueryGrid, TwinModel } from "../config/types";

export interface OverlayInfo {
  url: string | null;
  categorical: boolean;
  rectangle: Bounds | null;
}

interface QueryResult {
  lon: number;
  lat: number;
  value: number | null;
  place: string;
  explanation: string;
}

interface State {
  year: number;
  layer: string;
  summary: LayerSummary | null;
  twin: TwinModel | null;
  twinObject: string;
  queryGrid: QueryGrid | null;
  queryGridKey: string;
  query: QueryResult | null;
  notice: string | null;
  chinaBoundaryVisible: boolean;
  regionCases: RegionCase[];
  regionAnalysis: Record<string, RegionAnalysis>;
  selectedRegionId: string;
  serviceScenario: ServiceScenario | null;
  caseActive: boolean;
  loading: boolean;
  error: string | null;
}

export const useResilienceStore = defineStore("resilience", {
  state: (): State => ({
    year: 2024,
    layer: "four_dim_er",
    summary: null,
    twin: null,
    twinObject: "region",
    queryGrid: null,
    queryGridKey: "",
    query: null,
    notice: null,
    chinaBoundaryVisible: true,
    regionCases: [],
    regionAnalysis: {},
    selectedRegionId: "",
    serviceScenario: null,
    caseActive: false,
    loading: false,
    error: null,
  }),

  getters: {
    bounds: (s) => s.summary?.bounds ?? null,

    availableYears(s): number[] {
      const configured = realDataConfig.displayYears ?? [];
      const summaryYears = s.summary?.years ?? [];
      return Array.from(new Set([...summaryYears, ...configured]))
        .filter((y) => FOUR_DIM_YEARS.includes(Number(y)))
        .sort((a, b) => Number(a) - Number(b));
    },

    selectedLayerMeta(s): LayerMeta | undefined {
      return s.summary?.layers.find((l) => l.id === s.layer);
    },

    selectedRegion(s): RegionCase {
      return s.regionCases.find((region) => region.id === s.selectedRegionId) ?? s.regionCases[0] ?? DEFAULT_REGION_CASE;
    },

    selectedRegionAnalysis(s): RegionAnalysis | null {
      const id = s.selectedRegionId || s.regionCases[0]?.id;
      return id ? s.regionAnalysis[id] ?? null : null;
    },
  },

  actions: {
    timelineStat(year: number | string, layer: string): LayerStat | null {
      return (
        this.summary?.timeline?.[String(year)]?.[layer] ||
        supplementalLayerStats?.[String(year)]?.[layer] ||
        null
      );
    },

    availability(layer: string, year?: number) {
      const y = year ?? this.year;
      return currentYearAvailabilityRaw(layer, y, (yy, l) => this.timelineStat(yy, l));
    },

    async init() {
      this.loading = true;
      this.error = null;
      try {
        const [summaryRes, twinRes, regionRes, analysisRes] = await Promise.all([
          fetch(`/data/layer_summary.json?v=${Date.now()}`, { cache: "no-store" }),
          fetch(`/data/twin_model.json?v=${Date.now()}`, { cache: "no-store" }),
          fetch(`/data/region_boundaries.geojson?v=${Date.now()}`, { cache: "no-store" }),
          fetch(`/data/region_analysis.json?v=${Date.now()}`, { cache: "no-store" }),
        ]);
        this.summary = await summaryRes.json();
        this.twin = await twinRes.json();
        if (analysisRes.ok) {
          const analysisFile = (await analysisRes.json()) as RegionAnalysisFile;
          this.regionAnalysis = analysisFile.regions ?? {};
        }
        if (regionRes.ok) {
          const collection = (await regionRes.json()) as RegionBoundaryCollection;
          this.regionCases = regionCasesFromBoundary(collection);
        }
        if (!this.availableYears.includes(this.year) && this.availableYears.length) {
          this.year = this.availableYears[this.availableYears.length - 1];
        }
      } catch (err) {
        this.error = err instanceof Error ? err.message : String(err);
      } finally {
        this.loading = false;
      }
    },

    setYear(year: number) {
      this.year = year;
      this.queryGridKey = "";
    },

    setLayer(layer: string) {
      this.layer = layer;
      this.queryGridKey = "";
    },

    setTwinObject(id: string) {
      this.twinObject = id;
    },

    async loadQueryGrid(): Promise<QueryGrid> {
      const key = `${this.layer}_${this.year}`;
      if (this.queryGridKey === key && this.queryGrid) return this.queryGrid;

      const availability = this.availability(this.layer, this.year);
      if (this.layer !== "ri" && !availability.available) {
        throw new Error(`该图层暂无 ${this.year} 年已转换查询网格。`);
      }
      const stat = this.timelineStat(this.year, this.layer);
      const queryPath =
        (stat?.queryGrid as string) ||
        (stat?.query_grid_path as string) ||
        `data/query_grids/${key}.json`;
      const response = await fetch(`/${queryPath.replace(/^\.?\//, "")}?v=${this.queryGridKey || key}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`查询网格不存在：${key}`);
      this.queryGrid = await response.json();
      this.queryGridKey = key;
      return this.queryGrid!;
    },

    sampleQueryGrid(grid: QueryGrid, lon: number, lat: number): number | null {
      const { west, south, east, north } = grid.bounds;
      if (lon < west || lon > east || lat < south || lat > north) return null;
      const x = Math.round(((lon - west) / (east - west)) * (grid.width - 1));
      const y = Math.round(((north - lat) / (north - south)) * (grid.height - 1));
      return grid.values[y]?.[x] ?? null;
    },

    setQuery(result: QueryResult | null) {
      this.query = result;
      if (result) this.notice = null;
    },

    setNotice(text: string | null) {
      this.notice = text;
    },

    setChinaBoundaryVisible(visible: boolean) {
      this.chinaBoundaryVisible = visible;
    },

    setSelectedRegion(id: string) {
      this.selectedRegionId = id;
      this.caseActive = false;
      this.query = null;
    },

    setServiceScenario(scenario: ServiceScenario) {
      this.serviceScenario = scenario;
    },

    startLinkedRiskCase() {
      if (!this.selectedRegionId) {
        this.notice = "请先在区域治理与教学案例中选择一个区县。";
        return;
      }
      const targetYear = this.availableYears.includes(2024) ? 2024 : this.availableYears[this.availableYears.length - 1] ?? this.year;
      this.year = targetYear;
      this.layer = CASE_LAYERS[0] ?? "four_dim_fri";
      this.queryGridKey = "";
      this.caseActive = true;
      const region = this.selectedRegion;
      this.notice = `${region.segment}${region.name}｜已启动“低韧性-高风险”联动识别：请依次核查 FRI、ER、ERD，并在地图上点击重点斑块生成证据。`;
    },

    openCaseLayer(layer: string) {
      this.layer = layer;
      this.queryGridKey = "";
      this.caseActive = true;
    },

    currentOverlay(): OverlayInfo {
      const categorical = CATEGORICAL_LAYERS.has(this.layer);
      const availability = this.availability(this.layer, this.year);
      const stat = this.timelineStat(this.year, this.layer);
      const rectangle =
        (stat?.bounds as Bounds | undefined) ||
        (stat?.rectangle as Bounds | undefined) ||
        spatialBounds() ||
        this.bounds;

      if (this.layer !== "ri" && !availability.available) {
        return { url: null, categorical, rectangle };
      }
      if (!stat?.available && this.layer !== "ri") {
        return { url: null, categorical, rectangle };
      }

      const entry = realDataYearEntry(this.layer, this.year);
      const configured =
        entry?.overlay || (stat?.overlay as string) || (stat?.png_path as string) ||
        `data/overlays/${this.layer}_${this.year}.png`;
      const urlVersion = `${this.layer}_${this.year}_${stat?.valid_count ?? stat?.validRatio ?? "v2"}`;
      const url = `/${configured.replace(/^\.?\//, "")}?v=${encodeURIComponent(urlVersion)}`;
      return { url, categorical, rectangle };
    },
  },
});
