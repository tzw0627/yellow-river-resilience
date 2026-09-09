from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
import rasterio


ROOT = Path(__file__).resolve().parents[2]
ALIGNED_DIR = ROOT / "data" / "processed" / "aligned"
DOCS_DIR = ROOT / "docs"
CSV_OUTPUT = DOCS_DIR / "processed_inventory.csv"
REPORT_OUTPUT = DOCS_DIR / "processed_quality_report.md"

HEADERS = [
    "文件名",
    "文件路径",
    "CRS",
    "尺寸",
    "分辨率",
    "波段数",
    "数据类型",
    "nodata",
    "有效像元数_band1",
    "总像元数_band1",
    "有效像元比例_band1",
    "最小值_band1",
    "P1_band1",
    "中位数_band1",
    "P99_band1",
    "最大值_band1",
    "状态",
    "异常说明",
]


EXPECTED_CRS = "EPSG:4326"
EXPECTED_WIDTH = 2005
EXPECTED_HEIGHT = 988
EXPECTED_RES = (0.00224578821, 0.00224578821)


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT)).replace("\\", "/")


def is_categorical_name(name: str) -> bool:
    return name.startswith("clcd_") or name.startswith("water_class_")


def inspect_raster(path: Path) -> dict[str, object]:
    issues: list[str] = []
    with rasterio.open(path) as ds:
        arr = ds.read(1, masked=True)
        total = arr.size
        valid_values = arr.compressed()
        valid_count = int(valid_values.size)
        valid_ratio = valid_count / total if total else 0.0

        if str(ds.crs) != EXPECTED_CRS:
            issues.append(f"CRS 不是 {EXPECTED_CRS}")
        if ds.width != EXPECTED_WIDTH or ds.height != EXPECTED_HEIGHT:
            issues.append("尺寸不符合统一网格")
        if not (
            abs(ds.res[0] - EXPECTED_RES[0]) < 1e-12
            and abs(ds.res[1] - EXPECTED_RES[1]) < 1e-12
        ):
            issues.append("分辨率不符合统一网格")
        if valid_count == 0:
            issues.append("band1 无有效像元")
        if valid_ratio < 0.01:
            issues.append("band1 有效像元比例低于 1%")

        stats = {
            "min": "",
            "p1": "",
            "median": "",
            "p99": "",
            "max": "",
        }
        if valid_count:
            values = valid_values.astype("float64")
            q = np.nanpercentile(values, [0, 1, 50, 99, 100])
            stats = {
                "min": float(q[0]),
                "p1": float(q[1]),
                "median": float(q[2]),
                "p99": float(q[3]),
                "max": float(q[4]),
            }

            if path.name.startswith("ndvi_") or path.name.startswith("evi_"):
                if stats["min"] < -1.05 or stats["max"] > 1.05:
                    issues.append("植被指数值域超出 [-1, 1] 附近")
            if path.name.startswith("water_class_"):
                unique = np.unique(valid_values)
                bad = [int(x) for x in unique if x not in (0, 1, 2, 3)]
                if bad:
                    issues.append(f"水体分类存在异常类别 {bad[:10]}")
            if path.name.startswith("clcd_"):
                unique = np.unique(valid_values)
                if len(unique) > 20:
                    issues.append("CLCD 分类值数量异常偏多")
            if is_categorical_name(path.name):
                if not np.all(np.equal(valid_values, np.round(valid_values))):
                    issues.append("分类图层出现非整数值")

        status = "通过" if not issues else "需复核"
        return {
            "文件名": path.name,
            "文件路径": rel(path),
            "CRS": str(ds.crs),
            "尺寸": f"{ds.width}x{ds.height}",
            "分辨率": f"{ds.res[0]:.12g};{ds.res[1]:.12g}",
            "波段数": ds.count,
            "数据类型": ";".join(ds.dtypes),
            "nodata": "" if ds.nodata is None else ds.nodata,
            "有效像元数_band1": valid_count,
            "总像元数_band1": total,
            "有效像元比例_band1": round(valid_ratio, 6),
            "最小值_band1": stats["min"],
            "P1_band1": stats["p1"],
            "中位数_band1": stats["median"],
            "P99_band1": stats["p99"],
            "最大值_band1": stats["max"],
            "状态": status,
            "异常说明": "；".join(issues),
        }


def write_csv(rows: list[dict[str, object]]) -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows: list[dict[str, object]]) -> None:
    total = len(rows)
    passed = sum(1 for r in rows if r["状态"] == "通过")
    review = total - passed
    grids = sorted(
        set((r["CRS"], r["尺寸"], r["分辨率"]) for r in rows),
        key=lambda x: str(x),
    )

    review_rows = [r for r in rows if r["状态"] != "通过"]
    low_valid = sorted(rows, key=lambda r: float(r["有效像元比例_band1"]))[:10]

    lines = [
        "# 处理后数据质量检查报告",
        "",
        "## 总览",
        "",
        f"- 检查目录：`{rel(ALIGNED_DIR)}`",
        f"- 输出清单：`{rel(CSV_OUTPUT)}`",
        f"- 栅格数量：{total}",
        f"- 通过：{passed}",
        f"- 需复核：{review}",
        "",
        "## 统一网格检查",
        "",
    ]

    for crs, size, res in grids:
        lines.append(f"- CRS `{crs}`，尺寸 `{size}`，分辨率 `{res}`")

    lines.extend(
        [
            "",
            "## 需复核项目",
            "",
        ]
    )

    if review_rows:
        lines.append("| 文件 | 状态 | 异常说明 |")
        lines.append("| --- | --- | --- |")
        for row in review_rows:
            lines.append(
                f"| `{row['文件名']}` | {row['状态']} | {row['异常说明']} |"
            )
    else:
        lines.append("未发现需要复核的项目。")

    lines.extend(
        [
            "",
            "## 有效像元比例最低的 10 个图层",
            "",
            "| 文件 | 有效像元比例 | 中位数 | P99 |",
            "| --- | ---: | ---: | ---: |",
        ]
    )
    for row in low_valid:
        lines.append(
            f"| `{row['文件名']}` | {row['有效像元比例_band1']} | {row['中位数_band1']} | {row['P99_band1']} |"
        )

    lines.extend(
        [
            "",
            "## 结论",
            "",
            "本报告用于确认统一处理后的栅格是否满足后续地图展示和生态韧性计算的基础要求。",
            "若所有图层均通过，下一步可以进入最小地图可视化 demo。",
            "若存在需复核项目，应先检查原始数据、nodata、重采样方法或输出命名规则。",
            "",
        ]
    )

    REPORT_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    paths = sorted(ALIGNED_DIR.glob("*.tif"))
    rows = [inspect_raster(path) for path in paths]
    write_csv(rows)
    write_report(rows)
    print(f"checked {len(rows)} rasters")
    print(f"wrote {CSV_OUTPUT}")
    print(f"wrote {REPORT_OUTPUT}")
    print(f"review {sum(1 for r in rows if r['状态'] != '通过')}")


if __name__ == "__main__":
    main()
