// 把旧前端 frontend/data/config/*.js（window.X = {...}）转换为 TS 模块（export const X = {...}）。
// 运行：node scripts/gen-config.mjs
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const srcDir = resolve(here, "../../frontend/data/config");
const outDir = resolve(here, "../src/config/generated");
mkdirSync(outDir, { recursive: true });

const files = [
  { in: "layerDataConfig.js", out: "layerDataConfig.ts", global: "LAYER_DATA_CONFIG" },
  { in: "layerSpatialConfig.js", out: "layerSpatialConfig.ts", global: "LAYER_SPATIAL_CONFIG" },
  { in: "layerStats2024.js", out: "layerStats2024.ts", global: "LAYER_STATS_2024" },
  { in: "layerStatsAligned.js", out: "layerStatsAligned.ts", global: "LAYER_STATS_ALIGNED" },
];

for (const f of files) {
  const raw = readFileSync(resolve(srcDir, f.in), "utf-8");
  const re = new RegExp(`window\\.${f.global}\\s*=`);
  const converted = raw.replace(re, `export const ${f.global} =`);
  const header = "// 本文件由 scripts/gen-config.mjs 自动生成，请勿手改。\n// eslint-disable\n";
  writeFileSync(resolve(outDir, f.out), header + converted, "utf-8");
  console.log("generated", f.out);
}
