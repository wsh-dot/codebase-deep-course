# Codebase Deep Course | 源码深度课程 Skill

这个仓库发布 `codebase-deep-course` Skill，帮助 AI 编程 Agent 把真实代码仓库写成循序渐进的中文学习课程。课程围绕用户动作、数据变化和源码证据展开，包含可运行实验、失败判读与迁移练习。

完整说明：[中文](README.zh.md) · [English](README.en.md)

## 当前发布

- 从入口追踪调用、异步边界、持久化、条件分支和失败路径，并把同一对象贯穿各章。
- 区分源码事实、教学简化、模拟演示和扩展设计；分别报告已实测与未实测范围。
- 提供固定提交或工作区的源码摘录工具、HTML 静态审计工具，以及 UTF-8 校验和可重复打包工具。
- 支持按需制作离线 HTML、深化已有课程，以及在用户要求时编写双语言实验。
- 包内 14 项单元测试已通过；课程的教学质量和浏览器交互仍需按实际产物验收。

## 安装

可安装的 Skill 是 [codebase-deep-course/](codebase-deep-course/) 子目录。支持从 GitHub 子目录安装的 AI IDE 可使用：

```text
https://github.com/wsh-dot/codebase-deep-course/tree/main/codebase-deep-course
```

也可以将这段话交给 AI IDE：

```text
请从 https://github.com/wsh-dot/codebase-deep-course/tree/main/codebase-deep-course 安装 Skill。
只安装 codebase-deep-course/ 子目录；安装后的根目录应直接包含 SKILL.md、references/、scripts/、assets/ 和 agents/。
仓库根目录的 README 文件是发布说明，不属于 Skill 包。
```

手动安装及依赖说明见 [中文说明](README.zh.md#安装) 或 [English README](README.en.md#installation)。

## 使用

```text
使用 $codebase-deep-course，为当前仓库编写从零到一的中文深度课程。
读者懂一些编程，但不熟悉这个系统。请追踪真实执行链、同一对象的数据变化和源码证据，给出可运行实验与失败判读。
```

Skill 提供写作与验证方法，不包含 WeKnora 的源码或现成课程。新项目的章节、组件和运行环境须以目标仓库和用户要求为准。

## 仓库结构

```text
codebase-deep-course/
├── README.md                 # GitHub 入口
├── README.zh.md              # 中文完整说明
├── README.en.md              # English guide
└── codebase-deep-course/     # 可安装的 Skill
    ├── SKILL.md
    ├── agents/
    ├── assets/
    ├── references/
    └── scripts/
```

## 验证

在仓库根目录运行：

```text
python -m unittest discover -s codebase-deep-course/scripts -p "test_*.py" -v
```

源码提取、审计和打包命令见 [中文说明](README.zh.md#源码证据与验收) 与 [English README](README.en.md#source-evidence-and-validation)。
