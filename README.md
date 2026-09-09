# 黄河智韧

黄河中下游滩区生态韧性数字孪生与遥感智能体平台。平台整合遥感专题图层、行政管理单元、气象站实测降水、洪水风险指数（FRI）、生态韧性评价、三维时序沙盘、智能体问答和研判报告生成能力。

## 核心能力

- **数字孪生一张图**：Cesium 固定沙盘、行政边界、遥感底图与专题栅格叠加。
- **三维降水演变**：19 个沿线气象站、2020 年 366 天逐日记录，蓝色雨柱随用户选择的日期动态升降。
- **降水—FRI 联合研判**：按站点采样 2020 年 FRI，结合实测降水计算联合风险分、建议响应等级和重点核查任务。
- **四维生态韧性**：综合韧性 ER、规模 ERS、密度 ERD、形态 ERM、洪水韧性 ERF 和洪水风险 FRI。
- **遥感智能体**：支持本地规则回答，也可接入 OpenAI 兼容模型。
- **成果输出**：生成 Word/PDF 研判报告。

## 技术架构

```text
Vue 3 + TypeScript + Pinia + Cesium + ECharts
                       │
                       ├── /data/*  静态空间数据
                       └── /api/*   FastAPI 服务
                                      ├── 智能体
                                      ├── 报告
                                      └── 数据查询
```

## 项目结构

| 路径 | 内容 |
| --- | --- |
| `web/` | Vue 3 前端、Cesium 三维地图和应急交互 |
| `server/` | FastAPI 接口、智能体和报告生成 |
| `frontend/data/` | 平台运行所需的边界、叠加图、查询网格、统计和实测降水数据 |
| `backend/scripts/` | 栅格处理、指标计算和气象数据构建脚本 |
| `docs/` | 数据清单、处理标准与质检记录 |

## 快速运行

需要 Node.js 20+ 和 Python 3.10+。

### macOS / Linux

```bash
chmod +x run.sh
./run.sh
```

### Windows PowerShell

```powershell
.\run-dev.ps1
```

启动完成后访问 [http://127.0.0.1:8000](http://127.0.0.1:8000)。首次运行会安装前后端依赖并构建前端。

## 手动开发

```bash
# 后端
cd server
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m uvicorn app.main:app --reload --port 8000

# 前端（另一个终端）
cd web
npm ci
npm run dev
```

Vite 开发地址为 `http://127.0.0.1:5173`，`/api` 与 `/data` 会代理到 FastAPI。

## 构建与验证

```bash
cd web && npm ci && npm run build
cd ../server && .venv/bin/python -m unittest discover -s tests -q
```

生产运行：

```bash
cd server
WEB_DIST_DIR=../web/dist .venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 智能体配置

复制 `server/.env.example` 为 `server/.env`，按需填写模型参数：

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

`.env` 和本地密钥不会提交。没有配置模型时，平台自动使用本地规则回答，其余功能可正常运行。

## 数据说明

仓库包含平台演示和运行所需的处理后数据，不包含原始大体量气象文件与中间遥感栅格。降水数据截至 2020 年，时间分辨率以日尺度为主，适合历史过程复盘与辅助研判，不能代替实时气象预警。

第三方遥感、气象和底图数据的对外使用应遵守各数据源授权与引用要求。
