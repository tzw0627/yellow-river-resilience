import axios from "axios";
import type { ChatMessage } from "../config/types";

const http = axios.create({ baseURL: "", timeout: 60000 });

export interface AgentStatus {
  provider?: string;
  llm_enabled: boolean;
  model: string | null;
  base_url: string | null;
  providers?: AgentProviderOption[];
  rag?: {
    documents: number;
    layers: string[];
    years: number[];
  };
}

export interface AgentProviderOption {
  id: string;
  label: string;
  configured: boolean;
  model: string;
  base_url: string;
}

export async function getAgentStatus(): Promise<AgentStatus> {
  const { data } = await http.get<AgentStatus>("/api/agent/status");
  return data;
}

export interface ChatPayload {
  messages: ChatMessage[];
  provider?: string;
  year?: number;
  layer?: string;
  regionId?: string;
  mode?: "analysis" | "teaching" | "governance" | string;
  learning_task_id?: string;
  prompt_type?: string;
  source?: string;
  teaching_context?: Record<string, unknown>;
  layer_summary?: Record<string, unknown> | null;
  query?: {
    lon: number;
    lat: number;
    value: number | null;
    place: string;
    explanation: string;
  } | null;
}

export async function chat(payload: ChatPayload): Promise<{ reply: string; llm_enabled: boolean; model?: string }> {
  const { data } = await http.post("/api/agent/chat", payload);
  return data;
}

/** 流式问答：逐段回调增量文本。 */
export async function chatStream(
  payload: ChatPayload,
  onDelta: (text: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/agent/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...payload, stream: true }),
    signal,
  });
  if (!response.body) {
    const text = await response.text();
    onDelta(text);
    return;
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    onDelta(decoder.decode(value, { stream: true }));
  }
}

export interface QueryPayload {
  layer: string;
  year: number;
  lon: number;
  lat: number;
}

export interface QueryResult {
  layer: string;
  label: string;
  year: number;
  lon: number;
  lat: number;
  value: number | null;
  explanation: string;
}

export async function queryPoint(payload: QueryPayload): Promise<QueryResult> {
  const { data } = await http.post<QueryResult>("/api/query", payload);
  return data;
}

export interface ReportPayload {
  year: number;
  layers: string[];
  title?: string;
  format: "docx" | "pdf";
  evidence?: unknown[];
}

/** 生成报告并触发浏览器下载。 */
export async function downloadReport(payload: ReportPayload): Promise<void> {
  const response = await http.post("/api/report", payload, { responseType: "blob" });
  const disposition = response.headers["content-disposition"] || "";
  const match = /filename="?([^"]+)"?/.exec(disposition);
  const filename = match ? decodeURIComponent(match[1]) : `report.${payload.format}`;
  const url = URL.createObjectURL(response.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
