# 🔄 TaskFlow-AI

> **Lightweight AI Agent Task Flow Orchestration Engine**
> 轻量级AI Agent任务流编排引擎

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-42%20Passed-success.svg)]()

**[English](#english)** | **[简体中文](#简体中文)** | **[繁體中文](#繁體中文)**

---

<a id="english"></a>

## 🎉 About

**TaskFlow-AI** is a zero-dependency, pure Python task flow orchestration engine designed for AI Agent workflows. It provides DAG-based dependency resolution, multiple execution strategies, and a rich terminal UI — all without any external packages.

### 💡 Why TaskFlow-AI?

- **Solves a real pain point**: AI Agents often need to execute complex multi-step tasks with dependencies, but lack a lightweight, unified orchestration tool
- **Inspired by** trending AI Agent projects on GitHub (agent orchestration, task planning, workflow engines)
- **100% independent development**: Original implementation with unique features not found in any existing project

### ✨ Key Differentiators

| Feature | TaskFlow-AI | Typical Alternatives |
|---------|-------------|---------------------|
| External Dependencies | **Zero** | 5-20+ packages |
| Installation | **Copy & Run** | pip install + resolve |
| DAG Engine | **Built-in** | Requires networkx |
| Terminal UI | **Rich ANSI** | Basic print |
| Execution Strategies | **3 modes** | Usually 1 |
| Code Size | **~1500 lines** | 5000+ lines |

## ✨ Core Features

- 🔄 **DAG-Based Dependency Resolution** — Automatic topological sorting with cycle detection
- ⚡ **Three Execution Strategies** — Sequential, Parallel, and Level-Based execution
- 🔁 **Smart Retry Mechanism** — Configurable retry count and delay on task failure
- ⏰ **Timeout Management** — Per-task timeout with thread-based enforcement
- 🔀 **Conditional Execution** — Run tasks only when conditions are met
- 📊 **Rich Terminal UI** — Colorful status display, progress bars, and execution reports
- 🏗️ **Fluent Builder API** — Chainable method calls for intuitive workflow definition
- 📋 **Event Callbacks** — Hook into task lifecycle events (start, complete, fail)
- 📦 **JSON Export** — Export workflow results and reports as structured JSON
- 🧪 **Comprehensive Tests** — 42 unit tests covering all core modules
- 🖥️ **CLI Interface** — Built-in commands: demo, quick, validate, info

## 🚀 Quick Start

### Requirements

- Python 3.8 or higher
- No external dependencies required!

### Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/TaskFlow-AI.git
cd TaskFlow-AI

# That's it! No pip install needed.
```

### Run Demo

```bash
PYTHONPATH=src python -m taskflow_ai demo
```

### Quick Usage

```python
import sys
sys.path.insert(0, "src")

from taskflow_ai.workflow import Workflow

# Create a workflow
wf = Workflow("my-pipeline", "My AI Agent Pipeline")

# Add tasks with dependencies
wf.add_task(
    "fetch_data",
    "Fetch data from API",
    handler=lambda task, results: {"records": 100},
    priority="high"
)

wf.add_task(
    "process_data",
    "Process and analyze data",
    handler=lambda task, results: {"processed": results["fetch_data"].output["records"] * 2},
    deps=["fetch_data"],
    priority="medium"
)

wf.add_task(
    "generate_report",
    "Generate final report",
    handler=lambda task, results: {"report": "done"},
    deps=["process_data"],
    priority="low"
)

# Execute and get results
results = wf.run()
print(f"Success: {results['success']}")
print(f"Completed: {results['completed']}/{results['total_tasks']}")
```

### CLI Commands

```bash
# Run demo workflow
PYTHONPATH=src python -m taskflow_ai demo

# Run a quick task
PYTHONPATH=src python -m taskflow_ai quick -n "hello" -d "Say hello"

# Show system info
PYTHONPATH=src python -m taskflow_ai info

# Show version
PYTHONPATH=src python -m taskflow_ai --version
```

## 📖 Detailed Guide

### Task Priority Levels

```python
wf.add_task("critical_task", priority="critical")  # Executes first
wf.add_task("high_task", priority="high")
wf.add_task("medium_task", priority="medium")       # Default
wf.add_task("low_task", priority="low")             # Executes last
```

### Retry on Failure

```python
wf.add_task(
    "unstable_api",
    handler=call_external_api,
    max_retries=3,       # Retry up to 3 times
    retry_delay=2.0,     # Wait 2s between retries
)
```

### Timeout Control

```python
wf.add_task(
    "slow_operation",
    handler=long_running_task,
    timeout=30.0,  # Max 30 seconds
)
```

### Conditional Execution

```python
def should_run(task, results):
    return results["check_data"].output.get("valid", False) > 50

wf.add_task(
    "expensive_analysis",
    handler=run_analysis,
    deps=["check_data"],
    condition=should_run,
)
```

### Event Callbacks

```python
def on_task_complete(task, result):
    print(f"Task {task.name} completed: {result.output}")

wf.on("on_task_complete", on_task_complete)
```

### Export Results

```python
# Execute and export to JSON
results = wf.run_and_export("report.json")
```

### Execution Strategies

```python
# Sequential: one task at a time in dependency order
wf.config(strategy="sequential")

# Parallel: all ready tasks run simultaneously
wf.config(strategy="parallel", max_workers=8)

# Level-based: tasks at same level run in parallel (default)
wf.config(strategy="level_based", max_workers=4)
```

## 💡 Design Philosophy

TaskFlow-AI was designed with these principles:

1. **Zero Dependencies** — Pure Python standard library, no installation friction
2. **Simplicity First** — Intuitive API that takes minutes to learn
3. **AI Agent Focus** — Built specifically for AI agent task orchestration patterns
4. **Observable** — Rich terminal output for debugging and monitoring
5. **Extensible** — Event callbacks and metadata for custom integrations

### Roadmap

- [ ] Async/await support for I/O-bound tasks
- [ ] Persistent workflow state (save/resume)
- [ ] Web dashboard for workflow monitoring
- [ ] Plugin system for custom task types
- [ ] Workflow template library
- [ ] Distributed execution support

## 📦 Project Structure

```
TaskFlow-AI/
├── src/taskflow_ai/
│   ├── __init__.py      # Package init & version
│   ├── __main__.py      # CLI entry point
│   ├── task.py          # Task model & state management
│   ├── dag.py           # DAG engine & dependency resolution
│   ├── executor.py      # Task execution engine
│   ├── workflow.py      # High-level workflow builder
│   └── ui.py            # Terminal UI & visualization
├── tests/
│   └── test_taskflow.py # 42 comprehensive tests
├── examples/
│   ├── research_pipeline.py   # AI research pipeline demo
│   └── scraping_pipeline.py   # Web scraping pipeline demo
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Quick steps:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'feat: add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<a id="简体中文"></a>

## 🎉 项目介绍

**TaskFlow-AI** 是一个零外部依赖的纯Python任务流编排引擎，专为AI Agent工作流设计。它提供基于DAG的依赖解析、多种执行策略和丰富的终端UI — 无需安装任何第三方包。

### 💡 为什么选择 TaskFlow-AI？

- **解决真实痛点**：AI Agent在执行复杂多步骤任务时，缺乏轻量级的统一编排工具
- **灵感来源**：GitHub上热门的AI Agent项目（Agent编排、任务规划、工作流引擎）
- **100%独立自研**：原创实现，具备现有项目中没有的独特功能

### ✨ 核心差异化优势

| 特性 | TaskFlow-AI | 常见替代方案 |
|------|-------------|-------------|
| 外部依赖 | **零** | 5-20+个包 |
| 安装方式 | **复制即用** | pip install + 依赖解析 |
| DAG引擎 | **内置** | 需要networkx |
| 终端UI | **丰富ANSI** | 基础print |
| 执行策略 | **3种模式** | 通常只有1种 |
| 代码量 | **~1500行** | 5000+行 |

## ✨ 核心特性

- 🔄 **基于DAG的依赖解析** — 自动拓扑排序，内置环检测
- ⚡ **三种执行策略** — 串行、并行、分层执行
- 🔁 **智能重试机制** — 可配置重试次数和延迟
- ⏰ **超时管理** — 每个任务独立的超时控制
- 🔀 **条件执行** — 仅在条件满足时运行任务
- 📊 **丰富的终端UI** — 彩色状态显示、进度条、执行报告
- 🏗️ **流畅的构建器API** — 链式调用，直观的工作流定义
- 📋 **事件回调** — 钩入任务生命周期事件
- 📦 **JSON导出** — 将工作流结果导出为结构化JSON
- 🧪 **完善的测试** — 42个单元测试覆盖所有核心模块
- 🖥️ **CLI接口** — 内置命令：demo、quick、validate、info

## 🚀 快速开始

### 环境要求

- Python 3.8 或更高版本
- 无需任何外部依赖！

### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/TaskFlow-AI.git
cd TaskFlow-AI

# 就这么简单！无需 pip install。
```

### 运行演示

```bash
PYTHONPATH=src python -m taskflow_ai demo
```

### 快速使用

```python
import sys
sys.path.insert(0, "src")

from taskflow_ai.workflow import Workflow

# 创建工作流
wf = Workflow("my-pipeline", "我的AI Agent流水线")

# 添加带依赖关系的任务
wf.add_task(
    "fetch_data",
    "从API获取数据",
    handler=lambda task, results: {"records": 100},
    priority="high"
)

wf.add_task(
    "process_data",
    "处理和分析数据",
    handler=lambda task, results: {"processed": results["fetch_data"].output["records"] * 2},
    deps=["fetch_data"],
    priority="medium"
)

wf.add_task(
    "generate_report",
    "生成最终报告",
    handler=lambda task, results: {"report": "done"},
    deps=["process_data"],
    priority="low"
)

# 执行并获取结果
results = wf.run()
print(f"成功: {results['success']}")
print(f"已完成: {results['completed']}/{results['total_tasks']}")
```

### CLI命令

```bash
# 运行演示工作流
PYTHONPATH=src python -m taskflow_ai demo

# 运行快速任务
PYTHONPATH=src python -m taskflow_ai quick -n "hello" -d "打个招呼"

# 显示系统信息
PYTHONPATH=src python -m taskflow_ai info

# 显示版本
PYTHONPATH=src python -m taskflow_ai --version
```

## 📖 详细使用指南

### 任务优先级

```python
wf.add_task("critical_task", priority="critical")  # 最先执行
wf.add_task("high_task", priority="high")
wf.add_task("medium_task", priority="medium")       # 默认
wf.add_task("low_task", priority="low")             # 最后执行
```

### 失败重试

```python
wf.add_task(
    "unstable_api",
    handler=call_external_api,
    max_retries=3,       # 最多重试3次
    retry_delay=2.0,     # 重试间隔2秒
)
```

### 超时控制

```python
wf.add_task(
    "slow_operation",
    handler=long_running_task,
    timeout=30.0,  # 最长30秒
)
```

### 条件执行

```python
def should_run(task, results):
    return results["check_data"].output.get("valid", False) > 50

wf.add_task(
    "expensive_analysis",
    handler=run_analysis,
    deps=["check_data"],
    condition=should_run,
)
```

### 事件回调

```python
def on_task_complete(task, result):
    print(f"任务 {task.name} 完成: {result.output}")

wf.on("on_task_complete", on_task_complete)
```

### 导出结果

```python
# 执行并导出为JSON
results = wf.run_and_export("report.json")
```

### 执行策略

```python
# 串行：按依赖顺序逐个执行
wf.config(strategy="sequential")

# 并行：所有就绪任务同时执行
wf.config(strategy="parallel", max_workers=8)

# 分层：同层任务并行执行（默认）
wf.config(strategy="level_based", max_workers=4)
```

## 💡 设计思路与迭代规划

TaskFlow-AI 的设计原则：

1. **零依赖** — 纯Python标准库，消除安装摩擦
2. **简洁优先** — 直观的API，几分钟即可上手
3. **AI Agent聚焦** — 专为AI Agent任务编排模式设计
4. **可观测** — 丰富的终端输出，便于调试和监控
5. **可扩展** — 事件回调和元数据支持自定义集成

### 迭代规划

- [ ] Async/await 支持 I/O 密集型任务
- [ ] 持久化工作流状态（保存/恢复）
- [ ] Web仪表板监控工作流
- [ ] 插件系统支持自定义任务类型
- [ ] 工作流模板库
- [ ] 分布式执行支持

## 📦 项目结构

```
TaskFlow-AI/
├── src/taskflow_ai/
│   ├── __init__.py      # 包初始化与版本
│   ├── __main__.py      # CLI入口
│   ├── task.py          # 任务模型与状态管理
│   ├── dag.py           # DAG引擎与依赖解析
│   ├── executor.py      # 任务执行引擎
│   ├── workflow.py      # 高层工作流构建器
│   └── ui.py            # 终端UI与可视化
├── tests/
│   └── test_taskflow.py # 42个综合测试
├── examples/
│   ├── research_pipeline.py   # AI研究流水线示例
│   └── scraping_pipeline.py   # 网页抓取流水线示例
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## 🤝 贡献指南

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

**快速步骤：**
1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/your-feature`)
3. 提交更改 (`git commit -m 'feat: 添加你的功能'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 创建 Pull Request

## 📄 开源协议

本项目基于 MIT 协议开源 — 详见 [LICENSE](LICENSE) 文件。

---

<a id="繁體中文"></a>

## 🎉 專案介紹

**TaskFlow-AI** 是一個零外部依賴的純Python任務流編排引擎，專為AI Agent工作流設計。它提供基於DAG的依賴解析、多種執行策略和豐富的終端UI — 無需安裝任何第三方套件。

### 💡 為什麼選擇 TaskFlow-AI？

- **解決真實痛點**：AI Agent在執行複雜多步驟任務時，缺乏輕量級的統一編排工具
- **靈感來源**：GitHub上熱門的AI Agent專案（Agent編排、任務規劃、工作流引擎）
- **100%獨立自研**：原創實現，具備現有專案中沒有的獨特功能

### ✨ 核心差異化優勢

| 特性 | TaskFlow-AI | 常見替代方案 |
|------|-------------|-------------|
| 外部依賴 | **零** | 5-20+個套件 |
| 安裝方式 | **複製即用** | pip install + 依賴解析 |
| DAG引擎 | **內建** | 需要networkx |
| 終端UI | **豐富ANSI** | 基礎print |
| 執行策略 | **3種模式** | 通常只有1種 |
| 程式碼量 | **~1500行** | 5000+行 |

## ✨ 核心特性

- 🔄 **基於DAG的依賴解析** — 自動拓撲排序，內建環檢測
- ⚡ **三種執行策略** — 串行、並行、分層執行
- 🔁 **智慧重試機制** — 可配置重試次數和延遲
- ⏰ **逾時管理** — 每個任務獨立的逾時控制
- 🔀 **條件執行** — 僅在條件滿足時執行任務
- 📊 **豐富的終端UI** — 彩色狀態顯示、進度條、執行報告
- 🏗️ **流暢的建構器API** — 鏈式呼叫，直觀的工作流定義
- 📋 **事件回呼** — 鉤入任務生命週期事件
- 📦 **JSON匯出** — 將工作流結果匯出為結構化JSON
- 🧪 **完善的測試** — 42個單元測試覆蓋所有核心模組
- 🖥️ **CLI介面** — 內建命令：demo、quick、validate、info

## 🚀 快速開始

### 環境要求

- Python 3.8 或更高版本
- 無需任何外部依賴！

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/TaskFlow-AI.git
cd TaskFlow-AI

# 就這麼簡單！無需 pip install。
```

### 執行演示

```bash
PYTHONPATH=src python -m taskflow_ai demo
```

### 快速使用

```python
import sys
sys.path.insert(0, "src")

from taskflow_ai.workflow import Workflow

# 建立工作流
wf = Workflow("my-pipeline", "我的AI Agent流水線")

# 新增帶依賴關係的任務
wf.add_task(
    "fetch_data",
    "從API獲取資料",
    handler=lambda task, results: {"records": 100},
    priority="high"
)

wf.add_task(
    "process_data",
    "處理和分析資料",
    handler=lambda task, results: {"processed": results["fetch_data"].output["records"] * 2},
    deps=["fetch_data"],
    priority="medium"
)

wf.add_task(
    "generate_report",
    "產生最終報告",
    handler=lambda task, results: {"report": "done"},
    deps=["process_data"],
    priority="low"
)

# 執行並取得結果
results = wf.run()
print(f"成功: {results['success']}")
print(f"已完成: {results['completed']}/{results['total_tasks']}")
```

### CLI命令

```bash
# 執行演示工作流
PYTHONPATH=src python -m taskflow_ai demo

# 執行快速任務
PYTHONPATH=src python -m taskflow_ai quick -n "hello" -d "打個招呼"

# 顯示系統資訊
PYTHONPATH=src python -m taskflow_ai info

# 顯示版本
PYTHONPATH=src python -m taskflow_ai --version
```

## 📖 詳細使用指南

### 任務優先級

```python
wf.add_task("critical_task", priority="critical")  # 最先執行
wf.add_task("high_task", priority="high")
wf.add_task("medium_task", priority="medium")       # 預設
wf.add_task("low_task", priority="low")             # 最後執行
```

### 失敗重試

```python
wf.add_task(
    "unstable_api",
    handler=call_external_api,
    max_retries=3,       # 最多重試3次
    retry_delay=2.0,     # 重試間隔2秒
)
```

### 逾時控制

```python
wf.add_task(
    "slow_operation",
    handler=long_running_task,
    timeout=30.0,  # 最長30秒
)
```

### 條件執行

```python
def should_run(task, results):
    return results["check_data"].output.get("valid", False) > 50

wf.add_task(
    "expensive_analysis",
    handler=run_analysis,
    deps=["check_data"],
    condition=should_run,
)
```

### 事件回呼

```python
def on_task_complete(task, result):
    print(f"任務 {task.name} 完成: {result.output}")

wf.on("on_task_complete", on_task_complete)
```

### 匯出結果

```python
# 執行並匯出為JSON
results = wf.run_and_export("report.json")
```

### 執行策略

```python
# 串行：依賴順序逐個執行
wf.config(strategy="sequential")

# 並行：所有就緒任務同時執行
wf.config(strategy="parallel", max_workers=8)

# 分層：同層任務並行執行（預設）
wf.config(strategy="level_based", max_workers=4)
```

## 💡 設計思路與迭代規劃

TaskFlow-AI 的設計原則：

1. **零依賴** — 純Python標準庫，消除安裝摩擦
2. **簡潔優先** — 直觀的API，幾分鐘即可上手
3. **AI Agent聚焦** — 專為AI Agent任務編排模式設計
4. **可觀測** — 豐富的終端輸出，便於除錯和監控
5. **可擴展** — 事件回呼和元資料支援自訂整合

### 迭代規劃

- [ ] Async/await 支援 I/O 密集型任務
- [ ] 持久化工作流狀態（儲存/恢復）
- [ ] Web儀表板監控工作流
- [ ] 外掛系統支援自訂任務類型
- [ ] 工作流模板庫
- [ ] 分散式執行支援

## 📦 專案結構

```
TaskFlow-AI/
├── src/taskflow_ai/
│   ├── __init__.py      # 套件初始化與版本
│   ├── __main__.py      # CLI入口
│   ├── task.py          # 任務模型與狀態管理
│   ├── dag.py           # DAG引擎與依賴解析
│   ├── executor.py      # 任務執行引擎
│   ├── workflow.py      # 高層工作流建構器
│   └── ui.py            # 終端UI與視覺化
├── tests/
│   └── test_taskflow.py # 42個綜合測試
├── examples/
│   ├── research_pipeline.py   # AI研究流水線範例
│   └── scraping_pipeline.py   # 網頁抓取流水線範例
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── README.md
```

## 🤝 貢獻指南

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解詳情。

**快速步驟：**
1. Fork 本倉庫
2. 建立功能分支 (`git checkout -b feature/your-feature`)
3. 提交變更 (`git commit -m 'feat: 新增你的功能'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 建立 Pull Request

## 📄 開源協議

本專案基於 MIT 協議開源 — 詳見 [LICENSE](LICENSE) 檔案。
