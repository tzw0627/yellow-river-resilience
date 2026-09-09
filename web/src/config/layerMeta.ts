import type { TreeModule } from "./types";

export const CATEGORICAL_LAYERS = new Set(["clcd", "water"]);

export const layerKeyToId: Record<string, string> = {
  ndvi: "ndvi",
  evi: "evi",
  clcd: "clcd",
  water: "water",
  nightLight: "ntl",
  longNtl: "ntl",
  gdp: "gdp",
  resilienceIndex: "ri",
  fourDimEr: "four_dim_er",
  fourDimErs: "four_dim_ers",
  fourDimErd: "four_dim_erd",
  fourDimErm: "four_dim_erm",
  fourDimErf: "four_dim_erf",
  fourDimFri: "four_dim_fri",
};

export const layerColors: Record<string, string> = {
  ndvi: "#6f8f36",
  evi: "#2f8c63",
  clcd: "#b45a37",
  water: "#1d6f88",
  ntl: "#d7a53f",
  gdp: "#8b5b31",
  ri: "#4a8e4f",
  four_dim_er: "#4d8f64",
  four_dim_ers: "#6f9842",
  four_dim_erd: "#3f7f67",
  four_dim_erm: "#367f75",
  four_dim_erf: "#337e8b",
  four_dim_fri: "#b63730",
};

export const FOUR_DIM_YEARS = [2000, 2005, 2010, 2015, 2020, 2024];

export const architectureTree: TreeModule[] = [
  {
    id: "remote-sensing-twin",
    title: "遥感数字孪生底座",
    subtitle: "多源时空数据底座",
    defaultOpen: false,
    categories: [
      {
        title: "土地利用/覆被变化数据",
        items: [{ key: "clcd", label: "CLCD", type: "layer", layerId: "clcd", dataKey: "clcd" }],
      },
      {
        title: "夜间灯光数据",
        items: [
          { key: "nightLight", label: "Night Light", type: "layer", layerId: "ntl", dataKey: "ntl" },
          { key: "longNtl", label: "LongNTL", type: "layer", layerId: "ntl", dataKey: "ntl" },
        ],
      },
      {
        title: "社会经济发展数据",
        items: [
          { key: "gdp", label: "GDP", type: "layer", layerId: "gdp", dataKey: "gdp" },
          { key: "landscan", label: "LandScan（人口）", type: "data", dataKey: "landscan" },
        ],
      },
      {
        title: "数字高程栅格模型",
        items: [{ key: "dem", label: "DEM", type: "data", dataKey: "dem" }],
      },
      {
        title: "植被指数",
        items: [
          { key: "ndvi", label: "NDVI", type: "layer", layerId: "ndvi", dataKey: "ndvi" },
          { key: "evi", label: "EVI", type: "layer", layerId: "evi", dataKey: "evi" },
        ],
      },
      {
        title: "水体数据",
        items: [{ key: "water", label: "Water", type: "layer", layerId: "water", dataKey: "water" }],
      },
      {
        title: "气象数据",
        items: [
          { key: "temperature", label: "气温数据", type: "data", dataKey: "temperature" },
          { key: "precipitation", label: "降水数据", type: "data", dataKey: "precipitation" },
          { key: "terraclimate", label: "TerraClimate 水文数据", type: "data", dataKey: "terraclimate" },
        ],
      },
    ],
  },
  {
    id: "resilience-assessment",
    title: "韧性智能评估层",
    subtitle: "指标计算与风险评估",
    defaultOpen: true,
    categories: [
      {
        title: "四维生态韧性评价",
        items: [
          { key: "fourDimEr", label: "四维综合生态韧性 ER", type: "layer", layerId: "four_dim_er", dataKey: "four_dim_er" },
          { key: "fourDimErs", label: "规模韧性 ERS", type: "layer", layerId: "four_dim_ers", dataKey: "four_dim_ers" },
          { key: "fourDimErd", label: "密度韧性 ERD", type: "layer", layerId: "four_dim_erd", dataKey: "four_dim_erd" },
          { key: "fourDimErm", label: "形态韧性 ERM", type: "layer", layerId: "four_dim_erm", dataKey: "four_dim_erm" },
          { key: "fourDimErf", label: "洪水韧性 ERF", type: "layer", layerId: "four_dim_erf", dataKey: "four_dim_erf" },
          { key: "fourDimFri", label: "洪水风险 FRI", type: "layer", layerId: "four_dim_fri", dataKey: "four_dim_fri" },
        ],
      },
    ],
  },
  {
    id: "service-layer",
    title: "应急研判与决策服务",
    subtitle: "实测降水·风险联动·会商输出",
    defaultOpen: false,
    categories: [
      {
        title: "实测降水应急研判",
        items: [],
      },
    ],
  },
];
