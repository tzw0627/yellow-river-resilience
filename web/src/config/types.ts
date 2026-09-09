export interface Bounds {
  west: number;
  south: number;
  east: number;
  north: number;
  center?: [number, number];
}

export interface LayerStat {
  available?: boolean;
  sourceYear?: number | string;
  validRatio?: number;
  valid_ratio?: number;
  min?: number;
  max?: number;
  mean?: number;
  median?: number;
  p90?: number;
  overlay?: string;
  png_path?: string;
  queryGrid?: string;
  query_grid_path?: string;
  file?: string;
  [key: string]: unknown;
}

export interface LayerMeta {
  id: string;
  label: string;
  unit?: string;
  description: string;
  direction?: string;
}

export interface LayerSummary {
  bounds: Bounds;
  years: number[];
  layers: LayerMeta[];
  timeline: Record<string, Record<string, LayerStat>>;
}

export interface QueryGrid {
  layer: string;
  year: number;
  width: number;
  height: number;
  bounds: Bounds;
  values: (number | null)[][];
}

export interface TwinState {
  ri: { median: number };
  ndvi: { median: number };
  evi: { median: number };
  summary: { level: string; text: string };
}

export interface TwinSegment {
  id: string;
  name: string;
  type: string;
  description?: string;
  stations?: string[];
  state: TwinState;
}

export interface TwinModel {
  region: TwinSegment;
  segments: TwinSegment[];
  stations: { id: string; name: string }[];
}

export interface TreeItem {
  key: string;
  label: string;
  type: "layer" | "data" | "action";
  layerId?: string;
  dataKey?: string;
  message?: string;
}

export interface TreeCategory {
  title: string;
  items: TreeItem[];
}

export interface TreeModule {
  id: string;
  title: string;
  subtitle: string;
  defaultOpen: boolean;
  categories: TreeCategory[];
}

export type GradientLegend = {
  type: "gradient";
  title: string;
  low: string;
  high: string;
  gradient: string;
  notes: string[];
};

export type CategoryLegend = {
  type: "categories";
  title: string;
  items: [string, string][];
};

export type LegendConfig = GradientLegend | CategoryLegend;

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}
