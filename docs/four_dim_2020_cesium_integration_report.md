# 四维生态韧性 2020 Cesium 接入验证报告

生成时间：2026-05-27

## 1. 计算产物

输出目录：`data/processed/four_dim_manual/2020/`

已生成 6 个 Float32 GeoTIFF，未覆盖 `data/processed/indices/` 中的旧 MVP RI 成果：

| 指标 | 文件 | 有效像元 | 有效比例 | min | median | p90 | max |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| ER | `er_2020.tif` | 424572 | 0.275987 | 0.0000 | 0.4621 | 0.9501 | 1.0000 |
| ERS | `ers_2020.tif` | 426784 | 0.277425 | 0.0000 | 0.5000 | 1.0000 | 1.0000 |
| ERD | `erd_2020.tif` | 426420 | 0.277189 | 0.0476 | 0.5586 | 0.7059 | 1.0000 |
| ERM | `erm_2020.tif` | 426784 | 0.277425 | 0.0002 | 0.7788 | 1.0000 | 1.0000 |
| ERF | `erf_2020.tif` | 426622 | 0.277320 | 0.1263 | 0.4669 | 0.5925 | 0.9800 |
| FRI | `fri_2020.tif` | 426622 | 0.277320 | 0.0200 | 0.5331 | 0.5575 | 0.8737 |

CLCD 2020 unique values：`[1, 2, 3, 4, 5, 7, 8]`，均属于脚本内置 CLCD 常见编码范围。

## 2. 指标质量检查

- ERS：有效像元 426784，median = 0.5000，不是全 0。
- ERM：median = 0.7788，P90 = 1.0000；未出现 median=1 且 P90=1 的严重饱和。
- FRI 与 ERF：query grid 抽样验证 `FRI + ERF ≈ 1`，最大绝对误差约 `0.0001`，误差来自 JSON 四舍五入。
- ER：min = 0，median = 0.4621，P90 = 0.9501，max = 1，存在明显空间分异。

## 3. 前端 PNG overlay

输出目录：`frontend/data/overlays/four_dim/`

已生成并验证 alpha 非全透明：

| 图层 | PNG | 尺寸 | 非透明像元 |
| --- | --- | ---: | ---: |
| four_dim_er | `four_dim_er_2020.png` | 1985x775 | 424572 |
| four_dim_ers | `four_dim_ers_2020.png` | 1985x775 | 426784 |
| four_dim_erd | `four_dim_erd_2020.png` | 1985x775 | 426420 |
| four_dim_erm | `four_dim_erm_2020.png` | 1985x775 | 426784 |
| four_dim_erf | `four_dim_erf_2020.png` | 1985x775 | 426622 |
| four_dim_fri | `four_dim_fri_2020.png` | 1985x775 | 426622 |

## 4. 前端 query grid

输出目录：`frontend/data/query_grids/four_dim/`

已生成：

- `four_dim_er_2020.json`
- `four_dim_ers_2020.json`
- `four_dim_erd_2020.json`
- `four_dim_erm_2020.json`
- `four_dim_erf_2020.json`
- `four_dim_fri_2020.json`

每个 query grid 均包含有效取值，不是全空网格。

## 5. `layer_summary.json`

已更新 `frontend/data/layer_summary.json`，新增 6 个图层 ID：

- `four_dim_er`
- `four_dim_ers`
- `four_dim_erd`
- `four_dim_erm`
- `four_dim_erf`
- `four_dim_fri`

`timeline["2020"]` 中每个四维图层均包含：

- `id`
- `name`
- `year`
- `png_path`
- `query_grid_path`
- `bounds`
- `min`
- `max`
- `mean`
- `median`
- `p90`
- `valid_count`
- `valid_ratio`
- `unit`
- `description`
- `direction`
- `available`
- `overlay`
- `queryGrid`

FRI 的 `direction` 为 `higher_is_risk`，其余五个指标为 `higher_is_better`。

## 6. Cesium 前端接入

已修改 `frontend/app.js`：

- 在图层树中新增“四维生态韧性评价”分组。
- 新增 6 个图层入口：ER、ERS、ERD、ERM、ERF、FRI。
- 四维图层通过 `layer_summary.json` 中的 `overlay/png_path` 加载 PNG。
- 四维图层通过 `layer_summary.json` 中的 `queryGrid/query_grid_path` 加载点击查询网格。
- 右侧统计面板读取 `timeline[year][layer_id]` 的统计值。
- FRI 点击解释已写为“值越高表示洪水风险越高”。
- 新增四维图层颜色和图例。

静态检查：

- `node --check frontend/app.js`：通过。
- `python -m py_compile backend/scripts/calc_four_dim_from_local_dataset.py backend/scripts/import_four_dim_to_cesium_frontend.py`：通过。

## 7. 浏览器验证说明

当前环境无法完成真正的浏览器可视化截图验证：

- 启动 `python -m http.server` 时系统返回 `PermissionError: [Errno 1] Operation not permitted`。
- 尝试在 in-app browser 打开本地 `file://` 页面时被浏览器安全策略拦截。
- 因此本报告完成的是文件、数据、路径和 JS 语法级验证；Cesium 实际渲染建议在本机浏览器中通过 `python -m http.server 8080 -d frontend` 或项目 `run.ps1` 再做目视确认。

## 8. 结论

2020 年四维生态韧性指标已完成计算、前端 PNG/query grid 导入和 `layer_summary.json` 接入。旧 MVP RI 脚本与旧 `data/processed/indices/` 成果未被修改或覆盖。当前只跑通 2020 年，尚未默认批量计算 2000、2005、2010、2015、2020、2024。
