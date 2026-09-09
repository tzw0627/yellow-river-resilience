# 项目结构说明

## 设计原则

- **数据与代码分离**：原始数据在 `data/raw/`，可复现产品在 `data/processed/`
- **批处理与展示分离**：`backend/scripts/` 离线生成，`frontend/` 只读静态资源
- **中间地图区尺寸固定**：布局逻辑在 `frontend/styles.css`，Cesium 不得撑开三栏结构

## 数据流

```text
data/raw/*.tif
    → align_rasters.py
    → data/processed/aligned/
    → compute_resilience_index.py
    → data/processed/indices/
    → build_frontend_*.py
    → frontend/data/（JSON、PNG、tiles）
    → 浏览器 Cesium 展示
```

## 前端资源类型

| 类型 | 路径 | 用途 |
|------|------|------|
| 统计摘要 | `layer_summary.json` | 右侧面板、时间序列 |
| 孪生模型 | `twin_model.json` | 河段/整体 KPI |
| 边界 | `boundary_display.geojson` | Cesium 高亮（简化） |
| 单张叠加 | `overlays/{layer}_{year}.png` | 无瓦片时的回退 |
| 瓦片金字塔 | `tiles/{layer}/{year}/{z}/{x}/{y}.png` | 清晰缩放（推荐） |
| 点击查询 | `query_grids/{layer}_{year}.json` | 地图点击取值 |

## 不宜放入版本库的内容

- `frontend/config.js`（含 ion 令牌）
- 超大原始 GeoTIFF（可按需 LFS 或外置存储）
- `frontend/data/tiles/` 全量瓦片（体积大，建议本地或 CI 生成）
