# eval-lite

给一批问题和参考答案，并发跑多个模型，产出可对比的效果报告。

一个命令行工具：读 JSONL 数据 → 并发调模型 → 自动判分 → 出 CSV 明细和 Markdown 汇总。

## 快速开始

```powershell
uv sync

# 离线跑一遍（不联网、不花钱，用假模型验证整条流程）
uv run eval-lite run -i data/qa.jsonl -m fake

# 跑真模型
Copy-Item .env.example .env     # 然后填上 API 地址和密钥
uv run eval-lite run -i data/qa.jsonl -m qwen,glm -c 8
```

跑完在 `results/` 下得到两个文件：

- `results.csv` —— 每条样本一行（模型、答案、对错、延迟、错误信息）
- `report.md` —— 每个模型一行的横向对比

## 命令行参数

```
eval-lite run [OPTIONS]

  -i, --input        PATH   评测数据（JSONL，必填）
  -m, --models       TEXT   模型名，逗号分隔（必填）
  -c, --concurrency  INT    并发数（默认 8）
  -o, --output       PATH   输出目录（默认 results）
  -v, --verbose            打详细日志（DEBUG 级别）
```

## 输入格式

每行一个 JSON 对象：

```json
{"id": "q1", "prompt": "法国的首都是哪里？", "reference": "巴黎"}
```

空行会被跳过。坏数据（JSON 语法错、字段缺失、id 为空）会报错并**指出是文件的第几行**。

## 统计口径

**失败（请求超时、返回格式不对等）不计入准确率**，单独在「失败」列统计。

为什么这么选？因为「请求超时」和「答错了」是两件不同的事。混在一起算，
会让网络抖动看起来像模型变笨了。分开报，读的人才分得清该优化模型还是该修网络。

## 实测效果

> 这一节用你自己的真实数据跑一遍再填 —— **具体数字比任何形容词都有说服力**。

用假模型跑通整条流程（8 条样本，并发 4）：

```
跑完了：8 条结果（成功 8 条）
  明细：results/results.csv
  汇总：results/report.md
```

真模型的效果待补：

| 模型 | 样本数 | 准确率 | 平均延迟 |
| --- | ---: | ---: | ---: |
| *(待测)* | | | |

## 开发

```powershell
uv sync
uv run pytest              # 19 个测试
uv run ruff check .        # 代码检查
uv run pre-commit install  # 装提交钩子
```

CI 配在 `.github/workflows/ci.yml`，每次 push 会在 Ubuntu 上跑 ruff + pytest。

### 模块结构

| 模块 | 职责 |
| --- | --- |
| `models.py` | 全局数据模型（`Sample` / `Result`）—— 模块之间的接口约定 |
| `loader.py` | 读 JSONL，pydantic 校验，报错带行号 |
| `client.py` | 调模型。`HttpModelClient` 走网络，`FakeModelClient` 离线 |
| `runner.py` | 并发调度：Semaphore 限流、单条失败隔离、记录延迟 |
| `metrics.py` | 判分（归一化、exact match、contains match、准确率） |
| `report.py` | 出 CSV 和 Markdown |
| `config.py` | 从环境变量 / `.env` 读配置 |
| `cli.py` | 命令行入口，把上面这些接起来 |

### 几个设计决定

**依赖是参数传进来的。** `run_model(client, samples, ...)` 收一个客户端，
不认识具体是 HTTP 还是假的。这让整条流程能在离线状态下被测试和 CI 跑通。

**并发要限流。** `gather` 默认会把所有任务一把发出去 —— 1000 条就是 1000 个请求。
`Semaphore` 控制同时最多几个，并发数是配置项。

**失败不中断整批。** 单条失败记成 `Result(error=...)`，其余照常返回。
跑 1000 条时第 3 条超时，不该让前面 900 条白跑。

**模型之间串行、模型内部并发。** 如果模型之间也并发，总并发数会变成
「模型数 × concurrency」—— 你设 8，实际发 24 个请求。对 API 限流来说这个差别是致命的。
