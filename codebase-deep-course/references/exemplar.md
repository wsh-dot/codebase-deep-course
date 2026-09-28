# 深度示范与反例

这些是自包含的教学样例，不是新项目源码事实。用来校准写法，不要求照抄句子或技术栈。

## 浅写法为何不足

> 系统先解析文档，再分块，调用 Embedding 存入向量库。查询时召回、重排，最后调用大模型生成。图谱能提高准确率。使用 Langfuse 可以观察全链路。

这段只命名阶段。读者仍不知道数据长什么样、为什么需要不同存储、重排能解决什么、如何定位证据丢失，也不知道“全链路”是否真的有埋点。

## 改写示范：一条证据如何离开候选

### 本节要解决的问题

用户问：“清单 A 采用的规则如何处理材料 M？”答案却没有引用规则说明。我们沿一条证据检查，判断问题发生在召回、重排、上下文还是生成。

以下记录全部是虚构教学数据。`c-rule` 的原文写着“规则 R 要求核对材料 M 的规格和适用条件”；`c-project` 写着“清单 A 采用规则 R”。两条共同支撑答案，单独一条不足以证明完整的适用关系。

### 先认识数据

```json
{"chunk_id":"c-rule","source":"规则说明.md","version":"demo-v1","text":"规则R要求核对材料M的规格和适用条件。"}
```

`chunk_id` 关联同一证据，`source` 便于回原文，`version` 防止混入旧规则。排名可以变化，身份不应因为重新排序而改变。引用 `[1]` 只是本次回答的展示编号，不是长期身份。

### 逐步看候选变化

| 阶段 | 列表（从前到后） | 能判断什么 |
|---|---|---|
| 召回 | c-project, c-rule, c-old | 规则证据已经进入候选 |
| 重排 | c-rule, c-project, c-old | 规则更靠前，但尚未保证进入提示词 |
| 上下文，K=1 | c-rule | 项目采用关系被预算/数量限制排除 |
| 模型输入 | 只有规则说明 | 模型缺少“清单 A 采用 R”的依据 |

重排只对收到的候选判断相关性，不能把从未召回的片段补回来。即使重排成功，之后的截断仍可能让答案失去必要证据。这里改用更强的生成模型并不能补出缺少的项目采用关系。

### 完整教学函数

下面是刻意简化的教学实现：预算按 Unicode 码点计算，不是 token 预算，不是产品源码。预先按相关性排序；预算不足时跳过整个片段，不截断句子。真实服务还需计入系统提示词、问题和预留输出。

```python
def pack_context(ranked, max_chars):
    parts, citations, seen = [], [], set()
    used = 0
    for hit in ranked:
        if hit['chunk_id'] in seen:
            continue
        piece = f"[{len(citations) + 1}] {hit['text']}"
        cost = len(piece) + (1 if parts else 0)
        if used + cost > max_chars:
            continue
        parts.append(piece)
        citations.append(hit['chunk_id'])
        seen.add(hit['chunk_id'])
        used += cost
    return {'text': '\n'.join(parts), 'citation_ids': citations}
```

```javascript
function packContext(ranked, maxChars) {
  const parts = [], citations = [], seen = new Set();
  let used = 0;
  for (const hit of ranked) {
    if (seen.has(hit.chunk_id)) continue;
    const piece = `[${citations.length + 1}] ${hit.text}`;
    const cost = Array.from(piece).length + (parts.length ? 1 : 0);
    if (used + cost > maxChars) continue;
    parts.push(piece);
    citations.push(hit.chunk_id);
    seen.add(hit.chunk_id);
    used += cost;
  }
  return {text: parts.join('\n'), citation_ids: citations};
}
```

### 怎样读这个函数

`ranked` 由重排阶段传入；`parts` 保存实际发送的证据文本，`citations` 保存同一顺序的来源 ID。先检查重复，再计算加上引用标号后的成本；跳过的块不会进入引用映射。返回之后，生成函数必须使用 `text`，不能又改用未截断的旧候选列表。

JavaScript 使用 `Array.from` 计算码点数，避免 emoji 在 UTF-16 字符串长度中被算两次；这与 Python 的此处计数规则对应，但都不等于模型 token 数。

### 动手和判读

用文本为“规则R”的 `c-rule` 与“清单A”的 `c-project` 输入。第一片段 `[1] 规则R` 占 7 个码点，第二片段也是 7，加换行共 15。预算为 7 时仅保留 `c-rule`，预算为 15 时保留两条。将第一片段重复插入，`citation_ids` 仍不能重复。再试零预算，得到空文本与空引用，调用方应走资料不足路径。

这验证了边界行为，不代表真实资料只需 15 个 token。如果实验与手算不同，先检查引用前缀、换行和 Unicode 的计数，再查模型；此函数根本没有调用模型。

### 回到真实源码

在目标项目搜索上下文组装函数，从它的调用者确认收到的是哪一个候选字段，再检查返回文本怎样进入模型 messages。把核对到的连续原始片段、实际函数名和行号插入本位置。未读源码前，不给此教学函数编造一个产品路径。

### 应用题

召回记录里有 `c-rule`，最终 messages 中没有，是否应先增加检索 TopK？

参考判断：先比较重排输出和上下文入选列表，找出该 ID 离开的第一步。它已经被召回，盲目增加候选可能增加重排成本，却仍被同一预算截掉。应先解释丢失原因，再做单因素对照。

## 另外两种写法改进

### 部署说明

浅：启动 Docker，再运行 Compose，成功后上传。

深：区分引擎可用、配置可解析、服务健康、应用协议与业务验收。端口连通不能证明认证或写入成功；上传返回也不能证明索引完成。每步给当前目录、命令、预期字段、失败下一步，随后用同一短资料完成首次引用核对。

### 观测说明

浅：安装 SDK 并开启 Langfuse，就能看到所有步骤。

深：先查已有埋点，明确 root、子 span、generation 及未覆盖边界。说明上下文怎样穿过异步队列、流结束何时关闭观察、退出前怎样 flush。固定响应练习只验证树结构；真实接收端还须查 trace ID、认证、后台处理和界面。不会自动看到未埋点查询或模型未返回的内部推理。

## 原课程校准信息

WeKnora 最终案例包含九章，约 3,000–5,600 汉字/章正文，68 个深入小节、45 段核验摘录、11 张执行图、30 道选择应用题与18道推演题。这些是历史参考规模，不是每次都要复制的验收数字。价值在于各章都有原理、数据变化、操作判读、源码连接和完整函数。
