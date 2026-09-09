# 数据预处理统一标准

## 目标

将 `data/raw/` 中的多源遥感、气候、水文、人口和经济数据整理为统一空间基准的数据产品，供后续地图可视化、生态韧性指标计算和智能体查询使用。

## 输入数据

原始数据目录：

```text
data/raw/
```

数据清单：

```text
docs/data_inventory.csv
```

研究区边界：

```text
data/raw/boundary/yellow_river_floodplain_boundary.geojson
```

## 统一空间标准

### 坐标系

统一输出坐标系：

```text
EPSG:4326
```

选择原因：

- 适合 Cesium、Leaflet、Mapbox、WebGIS 等前端地图服务。
- 当前 NDVI、EVI、DEM、水体、夜间灯光、人口和 TerraClimate 多数已是 EPSG:4326。
- 后续可直接用于前端地图范围查询和瓦片服务。

说明：

- EPSG:4326 适合可视化和 Web 服务。
- 如果后续要做严格面积统计，应另行转换到等面积投影，例如 CGCS2000 Albers。

### 统一范围

统一裁剪范围采用研究区边界的 WGS84 bbox：

```text
west  = 112.177287
south = 34.237112
east  = 116.678382
north = 36.454202
```

边界来源：

```text
data/raw/boundary/yellow_river_floodplain_boundary.geojson
```

说明：

- 该边界是从已裁剪的 CLCD 2025 栅格有效区域反推得到。
- 如果后续获得官方黄河滩区边界 shp/geojson，应替换当前边界。

### 目标分辨率

统一分析分辨率：

```text
0.00224578821 degrees
```

约等于：

```text
250 m
```

选择原因：

- 与 MODIS NDVI/EVI 250m 数据一致。
- 比 30m 数据更轻，适合快速计算和前端演示。
- 比 500m、1km、4.6km 数据更细，但不会改变这些数据的原始信息精度。

重要说明：

- 将 500m、1km、4.6km 数据重采样到 250m 只用于统一网格计算，不代表原始数据精度提升。
- 对外报告中应说明各数据源原始分辨率。

## 重采样规则

### 分类数据

使用：

```text
nearest
```

适用图层：

- CLCD 土地利用
- JRC 水体分类
- 其他离散分类栅格

原因：

- 分类值不能用双线性或三次卷积插值，否则会产生不存在的类别值。

### 连续数据

使用：

```text
bilinear
```

适用图层：

- DEM
- NDVI
- EVI
- 夜间灯光
- 人口
- GDP
- TerraClimate 各气候水文变量
- JRC 水体频率

原因：

- 连续变量允许空间插值。
- 双线性比最近邻更平滑，适合可视化和综合指数计算。

### 特殊处理建议

人口、GDP、夜间灯光存在长尾高值，进入指标计算前建议做：

```text
log1p(x)
```

NDVI/EVI 如存在异常值，应按合理范围裁剪：

```text
NDVI: -1 到 1
EVI: -1 到 1
```

## nodata 处理

统一原则：

- 保留原始 nodata。
- 输出栅格应显式写入 nodata。
- 指标计算时 nodata 不参与归一化、不参与均值、不参与权重计算。

建议输出 nodata：

```text
float32 连续数据：-9999
int/category 分类数据：0
```

## 输出目录

统一处理后的栅格输出到：

```text
data/processed/aligned/
```

后续可视化瓦片或 COG 输出到：

```text
data/processed/cog/
```

生态韧性指标输出到：

```text
data/processed/indices/
```

## 输出命名规则

统一格式：

```text
{layer}_{year}_epsg4326_250m.tif
```

示例：

```text
clcd_2025_epsg4326_250m.tif
ndvi_2025_epsg4326_250m.tif
evi_2025_epsg4326_250m.tif
water_class_2025_epsg4326_250m.tif
ntl_2024_epsg4326_250m.tif
population_2024_epsg4326_250m.tif
gdp_2023_epsg4326_250m.tif
terraclimate_2024_epsg4326_250m.tif
```

## 指标计算分组

### 抵抗力

可用数据：

- NDVI
- EVI
- CLCD 土地利用
- JRC 水体频率
- TerraClimate DEF 水分亏缺
- TerraClimate PDSI 干湿指数

### 恢复力

可用数据：

- NDVI 多年趋势
- EVI 多年趋势
- AET/PET
- Soil_mean_mm 土壤水分
- 土地利用生态用地变化

### 适应力

可用数据：

- 人口 LandScan
- GDP
- 夜间灯光 LongNTL
- DEM 派生坡度

## 展示图层与计算图层区分

### 可优先用于地图展示

- DEM
- CLCD
- NDVI
- EVI
- JRC 水体
- 夜间灯光
- 研究区边界

### 可优先用于指标计算

- NDVI
- EVI
- CLCD
- JRC 水体频率
- TerraClimate
- 人口
- GDP
- 夜间灯光
- DEM 派生坡度

### 暂不直接用于栅格综合指数

- 气象站 Excel

用途：

- 站点气候背景说明
- TerraClimate 或其他栅格气候数据验证
- 图表展示

## 预处理脚本规划

下一步脚本：

```text
backend/scripts/align_rasters.py
```

职责：

- 读取 `docs/data_inventory.csv`
- 筛选 GeoTIFF 数据
- 根据图层类型选择重采样方法
- 统一到 EPSG:4326
- 裁剪到研究区 bbox
- 输出到 `data/processed/aligned/`

后续脚本：

```text
backend/scripts/convert_to_cog.py
backend/scripts/compute_resilience_indices.py
```

## 当前推荐流程

1. 完成数据清单。
2. 按本文档确定统一处理标准。
3. 编写并运行 `align_rasters.py`。
4. 检查输出栅格范围、分辨率、nodata 和像元值。
5. 选择 3 到 5 个图层先做地图可视化 demo。
6. 再开始生态韧性综合指数计算。
