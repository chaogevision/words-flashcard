# Demo Gallery｜成品演示

这里放的是已经完成过的三、四年级场景闪卡，用于快速展示这套 Skill 能产出什么样的结果。

> 注意：`demo/` 是展示层，不属于 `assets/golden_set/`。Golden Set 只收录当前规范下正式批准、可作为生产基准的样张；历史演示图可能保留旧版连线、标签尺度或场景组织方式，因此不能替代 V2.2.2 的 Core / Adapter / QA 规范。

## 三年级上册

### G3A-U01-C01 — Approved reference

![G3A-U01-C01](grade3/G3A-U01-C01-approved.jpg)

用途：展示场景词汇、白色圆角标签、英文/IPA/中文三级信息，以及 `connector.v3.light` 的整体视觉方向。

## 四年级上册

### G4A-C05 — Family chores / 家务协作

![G4A-C05](grade4/G4A-C05-chores-family.jpg)

用途：展示多人动作场景、动作词与家庭任务的组合。该图属于历史成品，适合用于演示与反例审计，不自动视为当前 Golden Sample。

### G4A-C08 — Play / game / sports

![G4A-C08](grade4/G4A-C08-play-game-sports.jpg)

用途：展示户外运动类场景和多个可指认目标的布局方式。同样属于历史演示图，实际生产时应继续执行当前版本的连接线长度、标签尺寸和语义锚点 QA。

## 如何使用这些演示

- 给人看效果：直接浏览本目录。
- 给 Agent 学习风格：优先使用 `assets/golden_set/`，再把这里作为补充场景参考。
- 做 QA：可以用历史图对照当前规范，识别长连线、标签过小、抽象词硬映射等旧问题。
- 做新年级：不要复制这些图里的旧缺陷，仍以 `SKILL.md`、`core/` 和当前平台 Adapter 为准。

仓库中的演示图使用轻量预览尺寸，以避免 Git 仓库膨胀；正式生产文件应由各批次 Artifact Store 独立保存。
