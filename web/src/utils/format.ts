export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "--";
  const number = Number(value);
  if (Math.abs(number) >= 1000) return number.toLocaleString("zh-CN", { maximumFractionDigits: 0 });
  return number.toLocaleString("zh-CN", { maximumFractionDigits: 3 });
}

export function explainValue(layer: string, value: number | null | undefined): string {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "该位置暂无有效数据。";
  const v = Number(value);
  if (layer === "ri") {
    if (v >= 0.75) return "生态韧性较高，区域状态相对稳定。";
    if (v >= 0.55) return "生态韧性处于中等水平，具备一定恢复能力。";
    return "生态韧性偏低，建议关注植被、水体稳定性和人类活动压力。";
  }
  if (layer === "ndvi" || layer === "evi") {
    if (v >= 0.55) return "植被状态较好，可作为生态支撑区观察。";
    if (v >= 0.3) return "植被状态中等，适合结合水体和土地利用继续判断。";
    return "植被状态偏弱，需要关注裸地、建设扩张或水分胁迫影响。";
  }
  if (layer === "ntl") {
    if (v >= 30) return "夜间灯光强，人类活动和建设开发压力较高。";
    if (v >= 5) return "夜间灯光中等，存在一定城镇或交通活动影响。";
    return "夜间灯光较弱，人类活动强度相对较低。";
  }
  if (layer === "gdp") {
    if (v >= 30000) return "经济活动强度较高，适应能力和开发压力需同时关注。";
    if (v >= 5000) return "经济活动强度中等。";
    return "经济活动强度较低。";
  }
  if (layer === "four_dim_fri") {
    if (v >= 0.7) return `FRI 为 ${formatNumber(v)}，值越高表示洪水风险越高，该位置属于相对高风险区。`;
    if (v >= 0.4) return `FRI 为 ${formatNumber(v)}，值越高表示洪水风险越高，该位置风险处于中等水平。`;
    return `FRI 为 ${formatNumber(v)}，值越高表示洪水风险越高，该位置风险相对较低。`;
  }
  if (String(layer).startsWith("four_dim_")) {
    if (v >= 0.7) return `指数值为 ${formatNumber(v)}，表示该位置四维生态韧性表现较强。`;
    if (v >= 0.4) return `指数值为 ${formatNumber(v)}，表示该位置四维生态韧性处于中等水平。`;
    return `指数值为 ${formatNumber(v)}，表示该位置四维生态韧性相对较弱。`;
  }
  if (layer === "clcd") return `土地利用分类值为 ${formatNumber(v)}，可结合 CLCD 图例判断类型。`;
  if (layer === "water") return `水体分类值为 ${formatNumber(v)}，可结合 JRC 水体图例判断水体稳定性。`;
  return "已读取该位置当前图层值。";
}
