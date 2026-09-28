# 源码深度课程 Skill

`codebase-deep-course` 帮助 AI 编程 Agent 将真实仓库整理为能独立学习、运行和排障的中文课程。它源自 WeKnora 深度课程的编写经验，但不会把 WeKnora 的九章结构、Neo4j 或双向量库当作其他项目的默认要求。

可安装目录：[codebase-deep-course/](codebase-deep-course/)。仓库根目录的 README 只用于 GitHub 展示，不应复制进已安装的 Skill。

## 适用任务

- 从零到一学习陌生代码库：从用户动作和入口出发，追踪数据准备与使用两条主线。
- 深化已有教程：保留有效正文和稳定锚点，补齐原理、数据变化、完整函数、操作与结果判读。
- 制作离线阅读产物：按需输出自包含 HTML，并检查导航、进度、键盘、窄屏和打印。
- 编写实验：在用户要求时提供 Python 与 JavaScript 等双语言实现，并核对相同输入和失败语义。

课程应让学习者能够解释机制、运行最小链路、定位证据在哪一步丢失，以及判断实验结果能证明什么。Skill 本身不是 WeKnora 源码、现成课程或自动生成器。

## 核心方法

1. 记录受众、学习目标、目标仓库的提交与工作区状态、运行环境和必需组件。
2. 从路由、CLI 或任务入口追踪真实调用，建立“动作 → 输入 → 处理 → 输出/存储 → 条件与错误 → 源码证据”的表。
3. 按学习依赖组织课程；用稳定 ID 的同一案例展示跨边界数据变化。
4. 每个关键机制解释原因、执行、源码、实操、预期结果、失败诊断和迁移练习。
5. 将源码事实、教学简化、模拟演示、扩展设计分开标记；实测状态独立记录。
6. 交付前分别验收教学质量、源码证据、实验行为和阅读界面。

具体流程见 [SKILL.md](codebase-deep-course/SKILL.md)，各项深入规则按其中的路由读取。

## 安装

### 从 GitHub 子目录安装

支持 GitHub 子目录安装的 AI IDE，请使用：

```text
https://github.com/wsh-dot/codebase-deep-course/tree/main/codebase-deep-course
```

请确认安装后的 Skill 根目录直接包含 `SKILL.md`、`references/`、`scripts/`、`assets/` 和 `agents/`。仓库根地址用于阅读说明，自动安装时应指向上面的子目录。

### 手动安装到 Codex

先克隆仓库：

```text
git clone https://github.com/wsh-dot/codebase-deep-course.git
```

Windows PowerShell：

```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse -Force ".\codebase-deep-course\codebase-deep-course" "$env:USERPROFILE\.codex\skills"
```

macOS / Linux：

```bash
mkdir -p ~/.codex/skills
cp -R ./codebase-deep-course/codebase-deep-course ~/.codex/skills/
```

其他 AI IDE 使用其文档指定的 Skills 目录，复制整个 `codebase-deep-course/` 子目录即可。

## 调用示例

新建课程：

```text
使用 $codebase-deep-course，为当前仓库编写详细中文课程。
读者懂一些编程，但不了解这个系统。目标是学会完整执行链、独立运行并排障。
请用一个贯穿案例追踪真实数据和源码，提供可运行实验、预期结果、失败判读与练习。
交付 Markdown；如果需要离线 HTML，我会明确提出。
```

深化已有课程：

```text
使用 $codebase-deep-course 深化现有课程。保留已有正文与稳定锚点，先逐章找出因果解释、数据变化、源码连接、实验判读的缺口，再补足并更新导航和验收。
```

如果只给出无法访问的仓库地址，Agent 应说明源码尚未核验，并请求源码或提供明确标记的原理教程；不能编造函数、行号和实测结果。

## 源码证据与验收

证据工具需要 Python 3.9+；固定提交摘录还需要 Git。脚本仅使用 Python 标准库。下例中的路径和标记须替换为目标仓库中的真实值。

从固定提交提取连续源码，并生成可直接放进 HTML 的片段：

```text
python codebase-deep-course/scripts/extract_source.py --repo <目标仓库> --path src/example.py --revision <完整提交号> --start-marker "def build_context(" --lines 12 --output evidence/context.json --html-output evidence/context.html
```

起始标记必须只命中一次；也可以用 `--end-marker` 替代 `--lines`。未提交的教学代码须显式使用 `--worktree`，产物会标记为工作区来源，不会伪称固定提交。

审计课程 HTML：

```text
python codebase-deep-course/scripts/audit_course.py <course.html> --repo <目标仓库> --offline --require-revision --output evidence/audit.json
```

源码课程没有摘录时默认失败。只有任务已明确缩小为概念教程，才使用 `--allow-no-source`，并在交付时注明源码未核验。静态审计不能证明解释正确、浏览器交互可用或真实服务运行；这些需要结合 [验收标准](codebase-deep-course/references/acceptance.md) 检查。

## 开发与打包验证

在仓库根目录运行：

```text
python -m unittest discover -s codebase-deep-course/scripts -p "test_*.py" -v
python codebase-deep-course/scripts/package_skill.py codebase-deep-course dist/codebase-deep-course.zip
```

当前发布的 14 项单元测试已通过。打包器会拒绝非 UTF-8 文本，核对 ZIP 往返字节，并排除缓存目录。测试覆盖工具行为；它不等于对任意仓库生成课程的独立模型评测。

## 范围与限制

- 新项目的章节和技术组件以目标源码及用户要求为准；WeKnora 路线仅供参考。
- 模拟数据与固定结果只能证明教学实现的行为，不能代表真实模型或数据库效果。
- 缺少 Docker、模型或观测平台时仍可完成文档和可用实验，但需列出未实测项。
- 生成的离线 HTML 应在断网、桌面和窄屏、键盘与打印场景中实际检查。
