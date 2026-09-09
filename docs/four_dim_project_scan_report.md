# 四维生态韧性项目扫描报告

生成时间：2026-05-27

## 1. 当前项目目录结构

项目根目录：`/Users/tangzhenwei/Desktop/大赛项目2`

主要目录：

- `backend/scripts/`：栅格对齐、MVP RI、前端 PNG/query grid/twin model 等离线脚本。
- `data/raw/`：项目内原始与边界数据副本。
- `data/processed/aligned/`：已统一到 EPSG:4326 / 约 250 m 的基础对齐栅格。
- `data/processed/indices/`：旧 MVP 生态韧性成果。
- `docs/`：项目结构、处理规范、质量报告和数据清单。
- `frontend/`：原生 HTML/CSS/JS + CesiumJS 静态前端。
- `frontend/data/overlays/`：前端专题图层 PNG。
- `frontend/data/query_grids/`：前端点击查询 JSON 网格。
- `frontend/data/config/`：真实数据配置、空间范围配置和补充统计。

## 2. `data/processed/aligned/` 已有对齐栅格

已有 50 个基础对齐栅格，主要包括：

- CLCD：`clcd_2000/2005/2010/2015/2020/2024/2025_epsg4326_250m.tif`
- DEM：`dem_static_epsg4326_250m.tif`
- EVI：`evi_2000/2005/2010/2015/2020/2024/2025_epsg4326_250m.tif`
- GDP：`gdp_2000/2005/2010/2015/2020/2023/2024_epsg4326_250m.tif`
- LandScan/人口：`landscan_2000/2005/2010/2015/2020/2024_epsg4326_250m.tif` 与 `population_2000/2005/2010/2015/2020/2024_epsg4326_250m.tif`
- NDVI：`ndvi_2000/2005/2010/2015/2020/2024/2025_epsg4326_250m.tif`
- 夜间灯光：`ntl_2000/2005/2010/2015/2020/2024_epsg4326_250m.tif`
- TerraClimate：`terraclimate_2000/2005/2010/2015/2020/2024_epsg4326_250m.tif`
- 水体：`water_2000/2005/2010/2015/2020/2024_epsg4326_250m.tif`
- JRC 水体分类：`water_class_2000_2000` 至 `water_class_2025_2021`
- 水体频率：`water_frequency_2000_2021_epsg4326_250m.tif`

## 3. `data/processed/indices/` 已有 MVP RI 成果

该目录已有旧 MVP 生态韧性成果，本次工作只读、不修改、不覆盖：

- `adaptation_2025.tif`
- `recovery_2025.tif`
- `resilience_index_2025.tif`
- `resistance_2025.tif`

## 4. `frontend/data/overlays/` 现有 PNG 组织方式

现有 PNG 直接平铺在 `frontend/data/overlays/` 下，命名为：

```text
{layer}_{year}.png
```

示例：

- `ndvi_2020.png`
- `evi_2020.png`
- `clcd_2020.png`
- `water_2020.png`
- `ntl_2020.png`
- `gdp_2020.png`
- `ri_2025.png`

旧 MVP RI 只存在 `ri_2025.png`。

## 5. `frontend/data/query_grids/` 现有查询网格组织方式

现有查询网格直接平铺在 `frontend/data/query_grids/` 下，命名为：

```text
{layer}_{year}.json
```

每个 JSON 包含：

- `layer`
- `year`
- `source`
- `width`
- `height`
- `bounds`
- `values`

当前网格尺寸通常为 `200 x 99`。

## 6. `frontend/data/layer_summary.json` JSON 结构

顶层结构为：

- `bounds`：研究区范围与中心点。
- `years`：前端年份按钮列表，当前为 `[2000, 2005, 2010, 2015, 2020, 2025]`。
- `layers`：图层元数据数组，当前包括 `ndvi/evi/clcd/water/ntl/gdp/ri`。
- `timeline`：按年份组织的统计字典，结构为 `timeline[year][layer_id]`。

每个统计对象通常包含：

- `validRatio`
- `min`
- `median`
- `p90`
- `max`
- `available`
- `sourceYear`
- `file`

## 7. Cesium 图层读取逻辑

核心文件：`frontend/app.js`

关键逻辑：

- 架构树与图层列表：`architectureTree`
- 图层 ID 映射：`layerKeyToId`
- 可用性判断：`currentYearAvailability`
- overlay 路径：`getOverlayProvider`
- Cesium 图层更新：`updateThematicLayer`
- query grid 读取：`loadQueryGrid`
- 点击取值：`sampleQueryGrid` 与 `handleSceneClick`
- 右侧统计：`renderMetrics`
- 图例：`legendConfig` 与 `renderLegend`

## 8. 本地原始已裁剪数据目录

本地数据目录：`/Users/tangzhenwei/Desktop/智能体数据集_黄河滩区边界裁剪结果_最终`

子文件夹与 tif：

- `1.土地利用_CLCD_30m/`
  - `CLCD_2000_黄河滩区中下游边界.tif`
  - `CLCD_2005_黄河滩区中下游边界.tif`
  - `CLCD_2010_黄河滩区中下游边界.tif`
  - `CLCD_2015_黄河滩区中下游边界.tif`
  - `CLCD_2020_黄河滩区中下游边界.tif`
  - `CLCD_2024_黄河滩区中下游裁剪.tif`
- `2.夜间灯光_LongNTL_500m/`
  - `LongNTL_2000/2005/2010/2015/2020/2024_黄河滩区中下游边界.tif`
- `3.DEM_NASA_30m/`
  - `DEM_黄河滩区中下游边界.tif`
- `3.人口_LandScan_1km/`
  - `LandScan_2000/2005/2010/2015/2020/2024_黄河滩区中下游边界.tif`
- `4.GDP_1km/`
  - `GDP_2000/2005/2010/2015/2020/2023_黄河滩区中下游边界.tif`
- `5.NDVI_250m/`
  - `MODIS_NDVI_AnnualMean_2000/2005/2010/2015/2020/2024.tif`
- `6.EVI_250m/`
  - `MODIS_EVI_AnnualMean_2000/2005/2010/2015/2020/2024.tif`
- `7.水体_30m/`
  - `JRC_Water_Frequency_2000_2021.tif`
  - `JRC_waterClass_target_2000_data_2000.tif`
  - `JRC_waterClass_target_2005_data_2005.tif`
  - `JRC_waterClass_target_2010_data_2010.tif`
  - `JRC_waterClass_target_2015_data_2015.tif`
  - `JRC_waterClass_target_2020_data_2020.tif`
  - `JRC_waterClass_target_2024_data_2021.tif`
- `9.TerraClimate水文数据/`
  - `TanQu_TerraClimate_Core_2000/2005/2010/2015/2020/2024.tif`

TerraClimate 本轮只扫描记录，第一版四维韧性计算不参与。
