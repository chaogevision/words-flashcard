# 小学英语场景闪卡 Skill V2 — Agent Agnostic

这是一个**跨 Agent 的生产协议 + 可执行核心规范**，用于把小学英语教材词表转换为一致的场景闪卡。

V2 的目标不是绑定某个模型或某个工具，而是把系统拆成三层：

```text
CORE      产品规则、教学规则、视觉规范、QA 门槛（Agent 无关）
ENGINE    状态机、Prompt 编译、确定性合成、QA 与 Artifact Store 的可移植接口合同
ADAPTERS  不同 Agent / 图片生成器 / 文件系统的接入层
```

## 最重要的架构原则

1. **教材是事实源**：英文、IPA、中文、Unit 不允许图片模型自行改写。
2. **生成式内容与确定性内容分离**：AI 画场景；Composer 写文字、标签、连接线。
3. **Stage 01–11 是固定协议**：更换 Agent 不改变生产阶段。
4. **连接线采用 `connector.v3.light`**：浅灰蓝细线 + 极小冷灰蓝目标点 + 必要时才出现。
5. **QA 是硬门槛**：视觉好看不能抵消文字、映射、覆盖错误。

## 新 Agent 如何接入

先读：
1. `AGENT_CONTRACT.md`
2. `SKILL.md`
3. `core/workflow.md`
4. `adapters/generic/ADAPTER_TEMPLATE.md`

Agent 只需要提供以下能力中的对应实现：
- 结构化文本推理
- 文件读写
- 图片生成或图片编辑
- 确定性图像合成（推荐）
- 图片 QA / 视觉检查

能力缺失时，合同规定了必须如何降级或阻断，禁止静默跳过硬门槛。

## 版本

- Skill protocol: `2.2.2`
- Visual spec: `Flashcard Visual Spec V2`
- Connector: `connector.v3.light`
- Contract: `Agent Contract 1.0`


## Platform adapters
This package includes adapter-specific execution guidance. For Doubao Work, read `adapters/doubao_work/ADAPTER.md` before production; it adds larger label sizing, connector-length ceilings, stricter semantic-anchor QA, and text-contamination/style-drift guards based on observed outputs.


## Adapter routing in V2.2
Platform-specific corrections are isolated by adapter:
- Doubao Work -> `adapters/doubao_work/ADAPTER.md`
- Qwen Office / 千问办公 -> `adapters/qwen_office/ADAPTER.md`
- OpenAI -> `adapters/openai/ADAPTER.md`

Run-time rule order is `Agent Contract -> Core -> Active Adapter -> Task`. See `ADAPTER_ROUTING.md`.

The Qwen Office adapter was added after auditing a real generated batch. It focuses on card-type routing, abstract/function-word handling, connector shortening, semantic endpoint accuracy, context-label proximity, object differentiation, cutaway layouts, and Qwen-specific QA gates.


## Package completeness
V2.2.2 includes the previously implicit execution dependencies as explicit package artifacts:
- `core/design_tokens.json`;
- `engine/` interface contracts;
- Stage 07 `base_asset` schema;
- Stage 10 `repair_action` schema;
- collection schemas for VocabularyMaster/CardPlanSet;
- `assets/golden_set/` reference;
- strict manifest/hash/reference validation.
