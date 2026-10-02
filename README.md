# Words Flashcard｜小学英语场景闪卡

> 把小学英语教材词汇，变成孩子一眼能看懂、可以直接学习和打印的**场景化单词闪卡**。

[![Skill](https://img.shields.io/badge/Skill-v2.2.2-2563eb)](SKILL.md)
[![Protocol](https://img.shields.io/badge/Protocol-Agent--Agnostic-0f766e)](AGENT_CONTRACT.md)
[![Connector](https://img.shields.io/badge/Connector-v3.light-64748b)](core/connector_system_v3.md)

这个仓库不是一套固定图片模板，而是一套可复用的 **AI 教育内容生产 Skill**：输入教材词表，经过词汇校验、场景分组、插图生成、确定性排版和 QA，输出风格统一、教材信息准确的英语场景闪卡。

**适合：** 教师、家长、教辅内容创作者、AI 教育产品开发者，以及希望在 Codex / ChatGPT / 豆包工作 / 千问办公等 Agent 中批量生产教材闪卡的人。

## 效果预览

### 三年级上册

<table>
<tr>
<td width="50%"><img src="demo/grade3/G3A-C01-pets.jpg" alt="三年级 宠物场景闪卡"></td>
<td width="50%"><img src="demo/grade3/G3A-C02-school-garden.jpg" alt="三年级 校园花园场景闪卡"></td>
</tr>
<tr>
<td align="center">Pets｜宠物</td>
<td align="center">School Garden｜校园花园</td>
</tr>
</table>

### 五年级上册

<table>
<tr>
<td width="50%"><img src="demo/grade5/G5A-C20-plant-parts.jpg" alt="五年级 植物结构场景闪卡"></td>
<td width="50%"><img src="demo/grade5/G5A-C24-hiking-trip.jpg" alt="五年级 徒步旅行场景闪卡"></td>
</tr>
<tr>
<td align="center">Plant Parts｜植物结构</td>
<td align="center">Hiking Trip｜徒步旅行</td>
</tr>
</table>

👉 **[查看完整 Demo Gallery（10 张高清示例）](demo/README.md)**

---

## 它解决什么问题？

普通 AI 出图很容易出现这些问题：

- 单词、音标或中文被模型写错；
- 为了塞词而硬拼不自然的场景；
- 标签太小、连接线太长，画面像工程标注；
- 抽象词、关系词被错误地指向某个物体；
- 换一个 Agent，风格和质量就完全漂移；
- 一张图看起来漂亮，却不一定适合教学。

Words Flashcard 把这些问题拆成一套可执行的生产流程：**教材事实与 AI 绘图分离，场景生成与文字排版分离，最终通过 QA 硬门槛验收。**

## 你会得到什么？

一张正式闪卡通常包含：

- 教材原词、IPA、中文释义；
- 与词义匹配的儿童友好场景；
- 清晰的大字号标签卡；
- `connector.v3.light` 轻量语义连接线；
- 对动作词、关系词、抽象词采用不同的视觉表达方式；
- 可追踪的 Card ID、状态和 QA 记录。

## 工作方式

```text
教材词表
   ↓
词汇提取与校验
   ↓
按自然场景分组
   ↓
Scene Brief / Layout Spec
   ↓
AI 生成无教学文字底图
   ↓
Composer 确定性写入英文 / IPA / 中文 / 标签 / 连线
   ↓
视觉 + 文本 + 语义 QA
   ↓
Approved Flashcard
```

核心原则只有一句话：

> **让 AI 负责画画，让确定性系统负责教学事实。**

## 快速开始

### 1. 获取仓库

```bash
git clone https://github.com/chaogevision/words-flashcard.git
cd words-flashcard
```

### 2. 先验证 Skill 是否完整

```bash
python tools/validate_package.py . --strict
```

正常输出：

```text
PACKAGE VALIDATION: PASS
```

### 3. 让你的 Agent 从这里开始读

建议读取顺序：

1. [`SKILL.md`](SKILL.md) — 主执行入口
2. [`AGENT_CONTRACT.md`](AGENT_CONTRACT.md) — Stage 01–11 输入/输出合同
3. [`core/workflow.md`](core/workflow.md) — 完整生产流程
4. [`ADAPTER_ROUTING.md`](ADAPTER_ROUTING.md) — 根据当前平台加载对应 Adapter

如果你只是想了解项目效果，先看 **[Demo Gallery](demo/README.md)** 就够了。

## 多 Agent 适配

核心生产标准保持不变，各个平台只加载自己的适配层：

| 环境 | Adapter | 重点解决的问题 |
| --- | --- | --- |
| OpenAI / Codex | [`adapters/openai`](adapters/openai/ADAPTER.md) | 工具调用、文件与 Composer 流程 |
| 豆包工作 | [`adapters/doubao_work`](adapters/doubao_work/ADAPTER.md) | 标签偏小、长连线、视觉漂移、伪文字 |
| 千问办公 | [`adapters/qwen_office`](adapters/qwen_office/ADAPTER.md) | 卡型路由、抽象词映射、长连线、锚点准确性 |
| 其他 Agent | [`adapters/generic`](adapters/generic/ADAPTER_TEMPLATE.md) | 按合同实现新的适配层 |

运行时规则顺序：

```text
Agent Contract → Core → 当前平台 Adapter → 当前任务
```

## 为什么不是“让模型直接画一张带文字的图”？

因为教学内容不能靠概率生成。

本项目把生产层分开：

**生成层**负责人物、环境、动作、道具和氛围；**确定性层**负责单词、IPA、中文、标签、连接线、Card ID 与 QA。这样即使更换图片模型，也不会让教材事实随模型一起漂移。

## 项目结构

```text
words-flashcard/
├── SKILL.md                 # Skill 主入口
├── AGENT_CONTRACT.md        # 跨 Agent 输入 / 输出合同
├── core/                    # 教学、视觉、分组与 QA 核心规则
├── engine/                  # Prompt / Composer / QA / 状态机接口
├── schemas/                 # JSON Schema
├── adapters/                # OpenAI / 豆包 / 千问 / Generic 适配层
├── assets/golden_set/       # 当前规范下的正式基准样张
├── demo/                    # 面向用户的成品展示
└── tools/                   # 包完整性校验等工具
```

## Demo、Golden Set 有什么区别？

- **`demo/`**：给人看的成品展示，覆盖不同年级和场景类型。
- **`assets/golden_set/`**：给生产系统和 Agent 做严格视觉基准的正式批准样张。

Demo 好看不等于自动成为 Golden Sample；进入 Golden Set 仍需要符合当前版本全部 QA 规则。

## 当前版本

- Skill Protocol: **2.2.2**
- Agent Contract: **1.0**
- Visual Spec: **Flashcard Visual Spec V2**
- Connector: **`connector.v3.light`**
- Demo: **三年级上册 + 五年级上册**

## 文档

- [安装与 Codex 检查](INSTALLATION.md)
- [完整工作流](core/workflow.md)
- [视觉规范](core/visual_spec.md)
- [连接线规范](core/connector_system_v3.md)
- [QA 规则](core/qa_rules.md)
- [Adapter 路由](ADAPTER_ROUTING.md)
- [适配器验收清单](ADAPTER_CONFORMANCE_CHECKLIST.md)

## Roadmap

- [x] Agent-Agnostic Stage 01–11 协议
- [x] OpenAI / 豆包工作 / 千问办公 Adapter
- [x] 三年级上册场景闪卡 Demo
- [x] 五年级上册场景闪卡 Demo
- [ ] 更多年级教材案例
- [ ] 更完整的自动化 Composer
- [ ] 自动视觉 QA 与批量返修
- [ ] 更多 Agent / 图片工作流 Adapter

## 关于项目

这个项目来自真实的小学英语教材闪卡生产实践。规范不是一次性写出来的，而是在不同 Agent、不同年级和真实批量出图中持续发现问题、修正规则、沉淀而成。

如果你正在做 AI 教育内容生产，欢迎直接使用、测试并继续扩展新的 Adapter。