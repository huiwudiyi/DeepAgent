# DeepAgent


```commandline
**广告一下**

八字藏天机，命理见人生。解析五行喜忌、性格天赋、事业财运、
感情婚姻与人生走势，帮你看清自身优势，把握关键机遇，趋吉避凶，规划更顺的人生方向
```
<p align="center">
  <img src="tool/Fortune_telling.png" width="188">
</p>


DeepAgent 是一个面向中文文本创作任务的多阶段 Agent 框架初版，核心目标是把用户的自然语言写作需求拆解为可执行、可校验、可迭代优化的自动写作流程。

项目当前聚焦于文学/文本创作场景，包含意图识别、Query 改写、RAG 检索增强、证据抽取、Brief 生成、大纲规划、大纲审查、初稿生成、初稿批判、最终润色等模块。整体设计适合继续扩展为 Deep Research、Multi-Agent、Skill Graph 或复杂写作任务自动执行系统。

---

## 项目特点

- **配置驱动 Memory System**：通过 `agent_class.json` 定义状态字段，自动生成带 getter/setter/append/save 能力的状态类。
- **多阶段 Agent 链路**：每个阶段继承统一的 `BaseParser`，包含 `gen_prompt`、`parse_result`、`exceute` 三类核心逻辑。
- **RAG 增强生成**：支持 Query 改写、外部检索、证据抽取、基于证据生成最终结果。
- **写作任务规划**：支持把用户 Query 转成 Brief，再规划成结构化大纲。
- **批判-优化闭环**：支持 Planner Critic、Planner Opt、Draft Critic、Complete Writer 等流程。
- **DAG 执行模型雏形**：内置 `DAG` 与 `DAGNode`，可将复杂任务拆成依赖明确的执行图。
- **安全与校验层雏形**：包含 Guardrail、Validation、Correction 等模块，用于限制工具、过滤风险输入、修复输出格式。
- **可扩展 Skill Registry**：通过 StageSkillRegistry 描述不同阶段 Skill 的输入、输出、条件和执行关系。

---

## 目录结构

```text
DeepAgent/
├── README.md
├── LICENSE
├── examples/
│   └── main_Agent/
│       ├── agent_class.json          # MemorySystem 字段配置
│       ├── agent_prompt.json         # 各阶段 Prompt 配置
│       └── main_Agent.ipynb          # 示例执行 Notebook
└── source/
    ├── BaseParser.py                 # Agent 基类
    ├── IntentAgent.py                # 意图识别 Agent
    ├── RewriteQueryAgent.py          # Query 改写 Agent
    ├── RagEvidenceExtractAgent.py    # RAG 证据抽取 Agent
    ├── CompleteRagAgent.py           # 基于证据生成结果
    ├── BriefAagent.py                # 写作 Brief 生成
    ├── PlannerAgent.py               # 大纲规划
    ├── PlannerCriticleAgent.py       # 大纲审查
    ├── CompletePlannerAgent.py       # 大纲优化
    ├── DraftWriterAgent.py           # 初稿生成
    ├── DraftCriticleAgent.py         # 初稿审查
    ├── CompleteWriterAgent.py        # 最终润色
    ├── WebRetriever.py               # 外部检索接口封装
    ├── WebSummaryAgent.py            # 检索内容总结
    ├── creat_class_from_config.py    # 配置生成状态类
    ├── dag.py                        # DAG 任务图
    ├── llm_agent.py                  # LLM 调用封装
    ├── safety.py                     # 安全、校验、修复层
    ├── middleware.py                 # Middleware 示例
    └── sub_agent.py                  # SubAgent 管理
```

---

## 核心流程

DeepAgent 自由拼装执行流程， 里面设置 router()到具体流程中。

### 1. RAG 问答/抽取链路

适合「经典句子」「名言摘录」「需要依据检索证据回答」等任务。

```text
用户 Query
   ↓
RewriteQueryAgent
   ↓
WebRetriever
   ↓
RagEvidenceExtractAgent
   ↓
CompleteRagAgent
   ↓
最终结果
```

对应逻辑示例：

1. `RewriteQueryAgent` 判断是否需要搜索，并生成 `search_query`。
2. `WebRetriever` 根据检索 Query 获取外部证据。
3. `RagEvidenceExtractAgent` 从证据中抽取高置信内容。
4. `CompleteRagAgent` 基于 Evidence 生成最终结果。

---

### 2. 深度写作链路

适合「工作写作」「报告生成」「申请书」「长文创作」等复杂任务。

```text
用户 Query
   ↓
IntentAgent
   ↓
BriefAagent
   ↓
PlannerAgent
   ↓
PlannerCriticleAgent
   ↓
CompletePlannerAgent
   ↓
PlannerSearchQueryParser / WebSummaryAgent
   ↓
DraftWriterAgent
   ↓
DraftCriticleAgent
   ↓
CompleteWriterAgent
   ↓
最终稿
```

该链路强调：

- 先理解任务，而不是直接生成；
- 先生成 Brief，再生成大纲；
- 对大纲进行审查和优化；
- 必要时补充检索证据；
- 生成初稿后继续批判和润色；
- 最后输出满足验收标准的结果。

---

## 快速开始
### 注意下面
```bash
source/llm_agent.py  设置授权
source/WebRetriever.py  设置请求网页和信息
examples/main_Agent/agent_prompt.json  设置 意图体系
```
### 1. 克隆项目

```bash
git clone https://github.com/huiwudiyi/DeepAgent.git
cd DeepAgent
```

### 2. 安装依赖

当前仓库暂未提供 `requirements.txt`，可以先根据源码安装基础依赖：

```bash
pip install requests pandas tqdm json-repair
```

如果你需要运行 Notebook 示例，还需要：

```bash
pip install jupyter openpyxl
```

---

## 配置模型接口

模型调用入口在：

```text
source/llm_agent.py
```

你需要补充真实的模型服务地址和请求头：

```python
url = ""

headers = {
    # 自己设置
}
```

`LLMClient.generate_text()` 会把 Prompt 发送给模型，并默认从如下结构中解析模型返回内容：

```python
result["request_data"]["choices"][0]["message"]["content"]
```

因此模型服务建议兼容 OpenAI/DeepSeek/Qwen 类 Chat Completion 返回格式。

---

## 配置检索接口

外部检索入口在：

```text
source/WebRetriever.py
```

当前代码中以下内容需要按你的线上环境补齐：

```python
GET_INSTANCE_BY_SERVICE = ""
BNS_NAME = ""
AK = ""
SK = ""

def requestapi(host, word):
    # 自主开发
    return response

def process_result(response):
    # 自主开发
    return retriever_evidence
```

`web_retriever(query)` 预期返回结构类似：

```python
{
    "chunk_1": "检索到的文本片段",
    "chunk_2": "检索到的文本片段"
}
```

---

## Prompt 配置说明

`examples/main_Agent/agent_prompt.json` 管理多个阶段 Prompt，例如：

- `intent`：意图识别   【业务自定义】
- `rewrite`：检索 Query 改写
- `rag_extract`：证据抽取
- `rag_complete`：基于证据生成最终结果
- `brief`：生成写作任务书
- `planner`：生成文章大纲
- `planner_criticle`：审查大纲
- `planner_opt`：优化大纲
- `search_query`：判断大纲章节是否需要检索
- `web_summary`：总结检索证据
- `draft`：生成初稿
- `draft_criticle`：审查初稿
- `complete_writer`：最终润色

---

## DAG 任务图

`source/dag.py` 提供了基础 DAG 能力：

- 添加节点：`add_node`
- 添加依赖：`add_edge`
- 获取可执行节点：`get_ready_nodes`
- 标记完成：`mark_done`
- 判断是否全部完成：`all_done`
- 计算拓扑层级：`calculate_layers`
- 按层级打印任务图：`print_layer_info`
- 根据大纲构建任务图：`build_plan_dag`

适合把复杂写作任务拆成多个可并行或串行执行的子任务。

---

## 安全与校验层

`source/safety.py` 中包含三类能力：

### ConstraintLayer

用于控制工具访问、数据路径、敏感词、高危操作和调用预算。

### ValidationLayer

用于检查 JSON Schema、关键词覆盖、事实片段、规则校验和轻量评分。

### CorrectionLayer

用于状态快照、失败回滚、Payload 自动修复、逻辑修复和降级兜底。

这些模块适合后续接入到 Agent 执行器中，形成更稳定的生产级执行闭环。

---

## 当前待完善事项

项目仍处于初版框架阶段，建议后续补齐以下内容：

- [ ] 增加 `requirements.txt`
- [ ] 增加 `.gitignore`，忽略 `.idea/`、日志、数据文件、密钥文件
- [ ] 修正部分命名拼写，例如 `MemerySystem`、`BriefAagent`、`Criticle`
- [ ] 抽象统一的 Agent Runner，减少 Notebook 中的流程硬编码
- [ ] 给每个 Agent 增加单元测试
- [ ] 给 `LLMClient` 增加多模型适配层
- [ ] 给 `WebRetriever` 增加本地 mock，方便离线测试
- [ ] 增加标准输入输出协议，例如 `state -> state`
- [ ] 增加日志、异常码和错误恢复策略
- [ ] 增加 README 中的端到端 Demo

---

## 推荐演进方向

### 1. 从链式 Agent 升级为 DAG Executor

当前已经有 DAG 雏形，可以进一步升级为：

```text
Planner -> DAG Builder -> Executor -> Validator -> Writer
```

每个节点负责一个独立子任务，节点之间通过 Memory/State 传递信息。

### 2. 从 Prompt Registry 升级为 Skill Registry

把每个阶段封装为 Skill：

```python
StageSkill(
    stage="planner",
    skill_name="planner_generation_skill",
    input_keys=["query", "brief"],
    output_keys=["sections"]
)
```

这样可以根据任务类型动态加载不同 Skill。

### 3. 增加策略路由

根据用户 Query 自动选择：

- 简单生成链路
- RAG 抽取链路
- 深度写作链路
- 多 Agent 协作链路

### 4. 加入评测体系

建议增加：

- Prompt 输出格式正确率
- JSON 解析成功率
- RAG 证据覆盖率
- 事实一致性
- 初稿修改收益
- 最终满意度评分

---

## License

本项目使用 Apache-2.0 License。
