# StoryScope 视角下的 AI 小说系统研究方案与论文撰写草稿

> 基于《StoryScope视角下的AI小说系统研究与落地方案》文档提炼的五个研究问题（含新增的人类锚定评估RQ5），本文档给出可执行的实验方案（数据、预算、评估指标、时间排期）与对应的论文撰写草稿骨架。全部实验仅调用商用 LLM API / Embedding API，不涉及模型训练（LoRA/SFT/RLHF 均不在本方案范围内，仅作为落地方案的后续延伸提及）。

---

## 0. 总体研究定位

| 项目 | 内容 |
|---|---|
| 总主题 | AI 长篇小说生成系统中的一致性维持机制与成本-质量权衡：一项基于 API 的实证研究 |
| 目标 venue | ACL Findings / EMNLP Findings（系统性实证研究 + benchmark 分析）；若做成 system/demo 论文可投 AAAI/IJCAI demo track |
| 核心资源复用 | 文档中已设计的 `story_state` JSON schema、`retrieve_story_context` 伪代码、StoryJob 接口、StoryScope narratology checker 思路、ConStory-Bench 一致性检查框架 |
| 训练边界 | 仅调用 API（生成模型 API + embedding API + judge API），不做 LoRA/SFT/RLHF/DPO 训练；RQ3 中的"轻量分类器"若需严格排除训练，可替换为无监督聚类/散度分析 |

---

## 1. 五个研究问题总览

| ID | 研究问题 | 核心机制对比 | 主要产出 |
|---|---|---|---|
| RQ1 | 长上下文 vs. RAG 状态追踪，哪种机制更能维持跨章节一致性？ | 全文长上下文 vs. story_state+RAG检索 | 一致性错误率随章节距离的变化曲线 |
| RQ2 | Writer-Judge-Revise 自纠循环的边际收益是否递减？ | 0/1/2/3 轮修正 | 质量提升 vs. 风格同质化的权衡曲线 |
| RQ3 | 不同基座模型是否存在可识别的"AI小说指纹"，revise（他改/自改）能否降低其可分性？ | 原始草稿 vs. 他改修订 vs. 自改修订 vs. 人类语料 | 模型指纹可分性变化及机制归因 |
| RQ4 | "廉价drafter+强reviser"路由 vs. 单一强模型，同预算下谁更优？ | 全强模型 / 全廉价模型 / 路由组合 | 成本-质量帕累托前沿 |
| RQ5 | 生成流水线相对 StoryScope 人机可分性基线，缩小了多少 gap、代价几何？ | 人类原文 / AI原始草稿 / AI revise后文本 | 人机可分性 gap 轨迹 + 检测器置信度漂移 |

**统一叙事框架**：在不训练模型的前提下，通过编排层（orchestration）机制选择——检索策略（RQ1）、修正轮数（RQ2）、模型路由（RQ4）——而非模型本身，控制长篇生成的一致性-质量-成本三角权衡；RQ3 揭示这些编排选择（尤其 revise）对模型可识别风格指纹的副作用，直接关系到路由决策的可解释性（如果 revise 掩盖了模型差异，路由策略的可归因性会受影响）；RQ5 将上述所有编排层实验统一锚定到 StoryScope 已验证的人机可分性基线上，回答"这套流水线到底把生成-检测的军备竞赛推进了多远"。

五个 RQ 共享同一套基础设施（生成 pipeline、评估 pipeline），可流水线化执行，见第 5 节时间排期。**独立性说明**：RQ1/RQ2/RQ4 会复用同一批大纲与部分草稿（见 2.4 节），因此这些 RQ 的显著性检验并非完全独立样本；论文中报告 p 值/置信区间时需注明共享数据来源，并在 Discussion 中讨论多重比较问题（见 3.6 节）。

---

## 2. 共享实验基础设施

### 2.1 数据与素材

- **故事生成种子**：设计 5 个不同题材大纲（都市悬疑、玄幻、言情、科幻、历史），每个大纲包含 world_bible + 3-5 个角色卡 + global_arc + 已埋设的 3 个"契科夫的枪"（伏笔）。直接复用文档第 6 页的 JSON schema 结构。
- **每部小说规模**：10-20 章，每章 3,000-4,000 字（约 4k-6k token 输出），总长度 8-10 万字/部，与文档 MVP 目标一致。
- **模型池**（全部为 API 调用）：
  - Drafter/强模型：GPT-4.1、Claude Sonnet 4.6、Gemini 2.5 Pro
  - Drafter/廉价模型：DeepSeek-V4-Flash、GLM-5.1、Qwen3-14B（API 版本）
  - Reviser：Claude Sonnet 4.6（固定，用于主实验；RQ3 需额外跑"自我修订"对照组，见3节）
  - **Judge（已修订，避免自我偏好偏差）**：judge 模型必须与被评测的 drafter/reviser 池**完全不重叠**——采用 o系列模型（如 o4）作为主 judge，且额外用一个不同家族的第二 judge（如 Gemini 2.5 Pro，仅当它不在当日被评测的 drafter 池中）做交叉验证，报告两个 judge 间的一致性（Cohen's Kappa/Spearman相关）；若 judge 与某 drafter 同源不可避免，必须在该模型条件下额外做 20-30 篇的人工 plus-minus 抽检，报告 judge-human 一致性作为偏差校准。
  - Embedding：BGE-M3（一致性检索）、OpenAI text-embedding-3 或 Qwen3-Embedding（风格指纹）

### 2.2 生成 Pipeline（复用文档 Story Orchestrator 架构）

```
State Manager (story_state.json)
   → Retriever/RAG（角色/世界观/历史摘要/风格库四路检索）
   → Planner（scene plan / beat list）
   → Drafter（章节草稿）
   → Consistency Checker + Narratology Checker（issue 列表）
   → Reviser（结合 issues 生成 final_text）
   → State Manager 更新（写回 opened_chekhov_guns / resolved_items）
```

FastAPI 路由沿用文档中的 `/v1/story/generate` 接口，`mode` 参数扩展为 `plan/draft/revise/eval`，五个 RQ 复用同一套代码，仅改变调用策略（长上下文 vs RAG、修正轮数、模型路由、是否接入人类语料对照与检测器探针）。

### 2.3 评估指标体系

| 维度 | 指标 | 工具/方法 |
|---|---|---|
| 一致性 | 世界观违规数、角色OOC次数、伏笔遗漏率 | ConStory-style consistency checker（LLM-as-judge + 规则匹配） |
| 叙事质量 | StoryScope narratology checker 通过率（304项细分类别） | LLM-as-judge 打分 |
| 文本多样性/AI感 | MAUVE、distinct-n、story feature dispersion | 开源 MAUVE 实现 + n-gram 统计 |
| 风格可分性 | 模型指纹分类准确率/类间距离 | Embedding + kNN 或余弦相似度聚类 |
| 人工评估 | Best-worst scaling (5点量表, pairwise) | 小规模人工标注，协议见 2.5 节（不再是"若资源允许"的占位项） |
| 成本 | 实际 API token 花费（input/output 分别计） | 直接从 API 返回的 usage 字段统计 |
| 情节债务（新增） | 每章新增 vs 兑现的"契科夫的枪"数量差，随章节累积的未偿付情节债务曲线 | 直接复用 `story_state` schema 中 `opened_chekhov_guns`/`resolved_items` 字段统计，零额外调用成本 |
| 检测器置信度轨迹（新增） | 连续 AI-ness 概率（非二元 pass/fail），随修订轮次/路由策略的漂移与方差 | narratology checker 输出改为校准过的概率值；贯穿 RQ2/RQ3/RQ5 |
| 一致性半衰期（新增，可选） | "错误率达到设定阈值所需章节数"这一单一可比数字 | 由 RQ1 的错误率-章节距离曲线派生，便于跨论文/跨条件横向引用 |

**说明**："情节债务曲线"和"检测器置信度轨迹"为本方案在原文档基础上新增的原创指标，前者零成本复用已有数据结构，后者需与 2.1 节修订后的独立 judge 配合校准；"悬念/张力轨迹"（用续写多样性熵衡量吸引力）作为探索性指标列入 Future Work，因其有效性尚缺验证，本次不作为主要结论依据。

### 2.4 预算估算（复用文档定价数据）

- 每部小说全流程（生成+2轮修正+评估）约 12k+4k token/章 × 15章 ≈ 24万 token/部
- 5 个大纲 × 6 个模型（4 强 + 2 廉价代表）× 3 个 RQ 复用同批草稿 ≈ 30 部小说规模
- 强模型部分（GPT-4.1/Claude/Gemini）：约 $150-300/部 → 预留 $3,000-5,000
- 廉价模型部分（DeepSeek/GLM/Qwen）：约 $20-50/部 → 预留 $500-1,000
- Judge/评估调用（独立 judge + 交叉验证 judge，按草稿数量 × 修正轮数估算，双 judge 成本翻倍于原方案）：预留 $800-1,200
- RQ5 新增：StoryScope 检测器复现/调用 + 人类语料抽取匹配 + 盲测任务界面：预留 $300-500
- 人工评估（2.5节协议，每 RQ 20-30 篇 × 5 个 RQ，按每篇 $2-4 标注费估算）：预留 $600-1,000
- **总预算区间：约 $5,200-8,700**（较原方案上调约 $1,200-1,700，主因是独立 judge 交叉验证与人工评估协议从占位变为实际执行项；可根据实际拿到的 API 额度/赞助调整规模，缩减到 3 个大纲 × 4 个模型、人工评估仅覆盖最关键的 RQ2/RQ3 也可将预算压缩至约 $3,000 做 pilot）

### 2.5 人工评估协议（替代原"若资源允许"占位）

- **标注规模**：每个 RQ 抽取 20-30 篇（片段或完整章节，视 RQ 而定）用于人工 plus-minus 验证，覆盖全部 5 个 RQ，总计约 100-150 个标注单元。
- **标注者**：至少 2 名具备中文长篇网络文学/类型小说阅读经验的标注者（非项目组成员，避免研究者偏差），每单元双标注，冲突项由第三方仲裁。
- **标注界面**：pairwise best-worst scaling 或 5点量表打分，盲测文本来源（不显示模型名/是否revise/是否AI），呈现顺序随机化。
- **一致性指标**：报告标注者间一致性（Cohen's Kappa 或 Krippendorff's alpha），并计算 judge-human 一致性（Spearman相关/一致率）作为 LLM-as-judge 的偏差校准依据；若一致性过低（如 Kappa < 0.4），需在 Limitations 中明确说明并降低对纯 LLM-judge 结论的置信度表述。
- **成本与排期**：已计入 2.4 节预算与第5节时间排期（第4周末至第5周初执行）。

### 2.6 通用评估控制（贯穿全部 RQ，避免遗漏）

- **盲测与顺序随机化**：所有 LLM-judge 与人工评委在评分/排序任务中均不得看到文本来源标签（模型名、是否 revise、修正轮数），且呈现顺序随机化，避免位置/顺序偏差。此为 2.5 节人工评估协议与 RQ5 盲测任务的强制前提，also适用于 RQ1/RQ2/RQ4 的 LLM-judge 打分环节。
- **Checker 校准**：consistency checker 与 narratology checker 本身是 LLM-as-judge 实现，其输出（世界观违规数、OOC次数等）需要相对人工标注做 precision/recall 校准——从每个 RQ 的标注样本中抽取子集，人工复核 checker 的判定，报告校准后的 precision/recall，而非直接假设 checker 输出即为 ground truth。若校准结果显示 checker 存在系统性偏差（如漏报率过高），需在 Results 中对相应指标做保守解释。

---

## 3. 各 RQ 详细实验设计

### RQ1：长上下文 vs. RAG 状态追踪

**自变量**：上下文策略（长上下文 full-context / RAG 检索 story_state）× 章节距离（第1-5章 / 第6-10章 / 第11-15章 / 第16-20章）

**固定变量**：drafter 模型（选 1-2 个支持超长上下文的模型：Gemini 2.5 Pro、Claude Sonnet 4.6），大纲与角色设定，修正轮数（固定 1 轮避免与 RQ2 混淆）

**流程**：
1. 对每个大纲，用同一 drafter 模型分别跑 full-context 条件和 RAG 条件，生成完整 15-20 章。
2. 两条件均在每章生成后调用 consistency checker + narratology checker 打分。
3. 记录每章的世界观违规数、角色OOC数、伏笔遗漏数，按章节距离分箱统计。

**假设检验**：用混合效应模型（chapter distance 为固定效应，story为随机效应）比较两条件下错误率斜率差异；预期 RAG 条件错误率增长更平缓。**样本量说明**：每个模型×条件仅5个大纲对应5个story级随机效应聚类单元，方差成分估计难以稳定收敛，斜率差异的置信区间会较宽——报告时应明确给出效应量与CI，避免仅凭 p<0.05 声称"显著"；若资源允许应将大纲数扩展到8-10个以提升聚类单元数。

**长上下文压力测试局限**：15-20章约6-12万token，远未逼近所选模型的百万级上下文窗口，长上下文机制可能没有被真正"压力测试"到失效点，导致两条件差异被低估——建议在 pilot 结果允许的情况下扩展章节数至接近上下文极限区间，或在 Limitations 中明确讨论此局限。

**产出图表**：错误率-章节距离折线图（两条件对比，含置信区间带）+ token 成本对比柱状图（RAG通常更省token）。

**Future Work 延伸**：本方案5个大纲全为中文题材，"RAG优于长上下文"的结论是否是中文语料/模型特有现象还是通用规律尚未验证，建议后续加一组英文题材复现本 RQ 以提升普适性主张，本次不纳入主实验范围。

### RQ2：Writer-Judge-Revise 循环的边际收益

**自变量**：修正轮数（0/1/2/3轮）

**固定变量**：drafter+reviser模型对（固定用 1 组"cheap-drafter + strong-reviser"，如 DeepSeek-V4-Flash + Claude Sonnet 4.6，同时复用文档中的路由思路），同一批章节草稿作为0轮基线

**流程**：
1. 生成基线草稿（0轮修正）。
2. 对同一草稿分别跑1/2/3轮 judge→revise 循环，每轮独立保存文本快照。
3. 对每个快照跑 narratology checker 通过率、MAUVE（与人类小说语料对比）、distinct-n。
4. 用 LLM-as-judge 做 4 个版本（0/1/2/3轮）的 best-worst ranking。

**假设检验**：narratology 通过率随轮数变化的趋势——**仅4个轮次点（0/1/2/3），自由度极低，应明确定位为描述性趋势观察，而非严格的函数拟合/显著性声称**；MAUVE/distinct-n 是否在2轮后出现下降（同质化信号）。**混淆控制**：revise 可能同时改变文本长度，需要在计算 MAUVE/distinct-n 前对长度做归一化或匹配采样，避免长度变化本身成为多样性指标下降的混淆因素。

**产出图表**：质量指标 vs 轮数（趋势图，标注为描述性）+ 多样性指标 vs 轮数（是否下降，长度已控制）双轴图。

### RQ3：AI 小说模型指纹

**自变量**：生成模型（6个候选）× 处理阶段（原始草稿 / 固定reviser修订 / **自我修订对照**）

**固定变量**：同一 plan/beat list（保证内容变量受控，只有风格/表达因模型而异）

**流程**：
1. 用 6 个模型分别对同一批 scene plan 生成短篇（3,000-5,000字），得到 6×N 篇原始草稿。
2. 用固定 reviser 模型（Claude Sonnet 4.6）对每篇做 1 轮 revise，得到 6×N 篇"他改"修订稿。
3. **新增自我修订对照组**：让每个模型对自己的草稿做 1 轮 self-revise（同模型既是drafter又是reviser），得到 6×N 篇"自改"修订稿。这一组是区分"趋同于固定reviser风格"与"AI指纹本身被削弱"两种机制的关键：若"他改"组可分性大幅下降但"自改"组可分性基本不变，说明趋同只是reviser风格的产物而非指纹被真正抹除；若两组都下降，才能支持"revise 削弱指纹"这一结论。
4. **新增人类基线对照（RQ5，见下）**：从 StoryScope 的人类小说语料中抽取同题材、同章节位置片段作为第三个参照类，用于判断 AI 模型间可分性相对人类作者间自然风格差异的相对大小。
5. 用 embedding API 提取每篇文本的风格向量（可用滑动窗口取多段落均值）。
6. **主方法（避免训练）**：计算类间/类内余弦距离比值（Silhouette-like 分离度指标），比较原始草稿 / 他改 / 自改 / 人类语料四组的模型可分性。
7. **可选/严格排除训练时的替代**：若要报告分类准确率，可用无参数的 kNN（k邻近，非参数、无需训练权重的"训练"）作为轻量级验证，并报告留一法（leave-one-out）分类准确率的置信区间（考虑到 n≈5/类的小样本，功效很低，此处应作为描述性趋势而非独立显著性声称）。

**假设检验**：revise 后的类间分离度是否低于原始草稿（配对 permutation test，报告效应量与置信区间而非仅 p 值，因样本量小、功效低）；比较"他改"组与"自改"组的分离度差异以判断机制归因。

**产出图表**：t-SNE/UMAP 可视化（原始 / 他改 / 自改 / 人类语料 四组 embedding 分布）+ 分离度指标对比表（含置信区间）。

### RQ4：Model Router 成本-质量权衡

**自变量**：生成策略（全程强模型 / 全程廉价模型 / cheap-drafter+strong-reviser路由）

**固定变量**：总 token 预算上限（按文档 $168-288/部小说的量级设定三档预算：低/中/高）

**流程**：
1. 在每个预算档位下，用三种策略各生成 3-5 部完整小说（复用大纲池）。
2. 严格记录每部小说的实际 API 花费（input token × 价格 + output token × 价格）。
3. 用统一评估指标（consistency checker + narratology checker + judge打分）打分。
4. 绘制成本-质量散点图，拟合帕累托前沿。

**假设检验**：路由策略是否在中低预算档位下不劣于全强模型策略（非劣效检验，non-inferiority test，需预先设定非劣效界值 margin）；是否优于全廉价模型策略。**样本量说明**：每档位仅 3-5 部小说，非劣效检验在此样本量下功效很低，结论应谨慎表述为方向性趋势，并在 Limitations 说明检验功效不足，建议后续以更大样本复现。

**混淆控制（已修订）**：(a) 成本核算必须纳入 judge/checker 本身的调用成本（尤其 2.1 节修订后需双 judge 交叉验证，成本更高），而非仅统计 drafter/reviser 的 token 花费；(b) 三种策略必须固定相同的修正轮数（如统一 1 轮），否则"路由策略更优"可能只是 RQ2 揭示的"轮数效应"的混淆结果，而非路由本身的贡献——若要探究轮数×路由的交互，应作为独立的两因子设计明确声明，不能与本 RQ4 的单因子比较混在一起。

**产出图表**：成本(x轴) vs 质量得分(y轴) 散点图（含每点误差条，成本含judge调用费），三种策略用不同颜色/形状区分，标出帕累托前沿曲线。

**Future Work 延伸（不纳入本次主实验，方法论上留作后续）**：当前路由是全书固定的静态策略（cheap-drafter+strong-reviser不变），可扩展为逐章**动态路由器**——依据实时信号（未解决伏笔数、judge打分置信度、consistency checker冲突数）决定该章是否调用强reviser，形成contextual bandit式在线决策问题，与oracle后验最优路由和当前静态策略做regret对比。

### RQ5（新增）：人类锚定的盲测图灵测试

**动机**：RQ1-RQ4 均为"AI vs AI"内部比较，未回答核心问题——本文的生成流水线（RAG状态追踪+自纠循环+模型路由）相对 StoryScope 已验证的人类/AI 可分性基线（93.2% vs 68.4% macro-F1），到底把这个 gap 缩小了多少、代价几何？RQ5 将人类语料和检测器作为外部锚点纳入闭环，把四个孤立的工程对比统一为一条"生成-检测军备竞赛"叙事线，也让本文与 StoryScope（CCF-A原文）形成真正的因果延续关系。

**自变量**：文本来源（人类原文 / AI原始草稿 / AI revise后文本）

**流程**：
1. 从 StoryScope 10,272 部人类小说语料中，按题材与章节位置匹配抽取对照片段，构造三元组（人类原文 / AI 原始草稿 / AI 修订稿）。
2. 调用（或复现轻量版）StoryScope 的 304 类检测器作为统一 "AI-ness" 探针，对三元组打分，并贯穿 RQ2（观察修订轮次是否系统性降低被判定为AI的概率）与 RQ3。
3. 用第2.1节修订后的独立 judge + 小规模人工评委（协议见2.5节）做 pairwise "猜AI" 盲测任务（评估者对文本来源盲测且顺序随机化），与 embedding 可分度交叉验证。

**产出**：人机可分性 gap 随 revise 轮次/路由策略变化的轨迹图；检测器置信度（连续 AI 概率，而非二元 pass/fail）随处理阶段的漂移与方差。

### 3.6 跨 RQ 独立性与多重比较

RQ1/RQ2/RQ4 复用同一批 5 个大纲甚至部分同批草稿（见 2.4 节"3个RQ复用同批草稿"），这意味着：(a) 这些 RQ 的显著性检验不是完全独立样本，论文中报告效应量/CI 时需注明数据复用关系；(b) 若在 Results 中一次性报告 5 个 RQ 的多组假设检验，应做多重比较校正（如 Benjamini-Hochberg FDR），或至少在 Discussion 中明确讨论未校正的风险，避免"多重检验中总有一个显著"的假阳性被过度解读。

---

## 4. 论文撰写草稿骨架

### 标题（候选）

- 《API-Only 系统性评估：AI 长篇小说生成中的一致性机制、自纠循环与成本-质量权衡》
- *An Empirical Study of Consistency Mechanisms, Self-Revision Loops, and Cost-Quality Tradeoffs in API-Based Long-Form AI Fiction Generation*

### Abstract 草稿要点

1. 长篇 AI 小说生成面临的核心挑战：跨章节一致性、AI 味道（idiosyncrasy）、生成成本，以及生成文本与真实人类创作之间的可分性。
2. 本文通过纯 API 调用（无需训练）系统评估编排层（orchestration）机制——而非模型本身——如何控制一致性-质量-成本三角权衡：(a) 长上下文 vs RAG 状态追踪；(b) writer-judge-revise 循环的边际收益；(c) 模型风格指纹及其在他改/自改 revise 后的变化；(d) 廉价/强模型路由的成本-质量权衡；(e) 上述机制相对 StoryScope 已验证的人机可分性基线（93.2% vs 68.4% macro-F1），把这一 gap 缩小了多少、代价几何。
3. 主要发现（占位，待实验完成后填入）：RAG 在长距离一致性上优于纯长上下文且更省成本；修正循环在 1-2 轮后收益递减且可能引发同质化；不同模型存在可识别的风格指纹，revise 会降低但不会消除这种指纹（需区分趋同于reviser风格与指纹本身被削弱）；路由策略能在中低预算下逼近强模型质量；生成流水线缩小了人机可分性 gap 但未完全消除。
4. 贡献：(a) 一套可复现的 API-only 评估框架，含独立 judge 校准与人工验证协议；(b) 复用并扩展 StoryScope / ConStory-Bench 的评估协议，并将其检测器纳入闭环形成人类锚定评估；(c) 面向工业落地（Flowith/Manus 编排）的成本-质量决策依据。

### 章节结构

1. **Introduction**
   - AI 小说生成的落地需求与 StoryScope/ConStory-Bench 揭示的一致性与可分性问题
   - 现有工作的空白：多数研究关注短篇生成质量，缺乏长篇、多机制对比、成本视角、人类锚定的系统性实证研究
   - 本文的五个研究问题与贡献列表
   - **统一框架句（必须在Introduction结尾给出，避免被读成"多篇workshop paper拼接"）**："我们提出并验证：在不训练模型的前提下，编排层机制选择（检索策略、修正轮数、模型路由）而非模型本身，是控制长篇生成一致性-质量-成本三角权衡的主要杠杆；我们进一步将这些编排选择锚定到人机可分性这一外部效度指标上，以量化工程改进的实际收益。"

2. **Related Work**
   - 故事生成：Plan-and-Write、Fabula、StoryState、Hierarchical Neural Story Generation
   - **Agentic / multi-agent 写作系统（新增，原方案文献空白）**：Re3、DOC、AI Storyteller 等多智能体协作长篇生成工作，与本文 RQ1（检索策略）、RQ4（模型路由）的编排设计直接相关，需在此对比设计差异
   - 一致性评估：ConStory-Bench、StoryScope idiosyncrasy detection
   - 自纠/反思式生成：R2-Write、writer-judge-revise 范式
   - RAG 与长上下文对比的相关工作（引用检索增强生成的经典论文 + 长上下文模型技术报告）
   - 风格/AI文本检测：MAUVE、authorship classification 相关工作
   - **本文与 StoryScope/ConStory-Bench 的关系（新增独立段落，必须写，否则易被质疑"换壳"）**：明确区分——StoryScope 提出了 narratology checker 与一致性评估框架本身（评估工具的贡献）；本文将该框架作为固定探针，系统评估上游编排层机制（检索/修正/路由）对下游一致性、风格指纹和人机可分性的因果影响（机制归因的贡献），两者是"工具提出"与"工具应用于系统性机制研究"的互补关系，而非重复。

3. **Method / Experimental Infrastructure**
   - Story Orchestrator 架构图（复用文档第5张图的模块划分：State Manager / Retriever / Planner / Drafter / Reviser / Consistency Checker）
   - story_state schema 说明（引用文档 JSON 示例）
   - 五个 RQ 各自的实验设计（对应第3节内容精简版）
   - judge 校准与人工评估协议摘要（详见 2.1、2.5、2.6 节）

4. **Experimental Setup**
   - 模型池、大纲池、评估指标、预算表

5. **Results**
   - RQ1-RQ5 分别一节，图表+统计检验结果（含效应量与置信区间，样本量有限处明确标注为描述性趋势）

6. **Discussion**
   - 落地建议：MVP 阶段应优先采用 RAG+路由组合以控制成本
   - 跨 RQ 独立性与多重比较讨论（见 3.6 节）

7. **Limitations（独立章节，ACL/EMNLP 强制要求，不可并入 Discussion）**
   - LLM-as-judge 与人工评估的一致性未经大规模验证，仅基于每 RQ 20-30 篇的小规模校准（见 2.5 节）
   - 5 个大纲的题材代表性有限，跨语言/跨体裁泛化性未验证（见 RQ1 Future Work）
   - 模型池的可复现性风险：所用 API 模型可能被厂商静默更新版本，实验结果的时间戳与模型版本号需在附录中记录
   - 多个 RQ 样本量小（n≈5/类），统计检验功效低，相关结论应视为方向性趋势而非强显著性声称（见 3.6 节）
   - RQ3/RQ5 的"AI-ness"检测器本身可能存在系统性偏差，其 precision/recall 校准仅覆盖抽样子集（见 2.6 节）

8. **Ethics / Broader Impact Statement（独立声明，新增）**
   - **版权与训练语料**：本研究仅调用商用 API 进行推理，不训练模型，不直接使用受版权保护的小说文本进行模型训练；但需说明 API 提供商的底层模型训练语料版权状态不在本文控制范围内。
   - **生成内容滥用风险**：AI 生成长篇小说存在被用于冒充人类创作、批量内容农场化（content farming）投放平台的风险；RQ5 的检测器闭环研究客观上也可被滥用于"反向优化"AI 文本以规避检测——本文在方法部分不提供可直接部署的规避工具，仅报告聚合统计结果。
   - **对人类作者劳动市场的潜在影响**：低成本长篇 AI 小说生成能力可能冲击网络文学作者的经济生态，本文作为实证研究不代表对此类应用的倡导，呼吁下游落地方应用时考虑内容标注（AI生成标识）与作者权益保护机制。

9. **Conclusion**

### 需要人工补全的部分（占位标记）

- [ ] 具体实验结果数值与图表（需实际跑实验后填入）
- [ ] 人工评估已锁定协议（见2.5节），需在实验阶段确认标注者招募到位，而非退回"若资源允许"
- [ ] Related Work 中的具体引用格式（已有文档提供的 arXiv 链接可直接转 BibTeX），需补充 Re3/DOC 等 agentic 写作系统文献
- [ ] 数据/代码发布计划（Reproducibility Checklist）：需在投稿前确定生成的30部小说全文、评估脚本、prompt模板、judge/checker 校准数据是否可公开发布（涉及大纲原创性与人类语料版权，需与 StoryScope 数据方确认二次分发权限）

---

## 5. 时间排期（4-6周，衔接文档已有的 MVP 排期思路）

| 周次 | 任务 |
|---|---|
| 第1周 | 搭建共享基础设施：Orchestrator API、5个大纲与 story_state、评估 pipeline（checker + judge prompt模板） |
| 第2周 | RQ1 + RQ4 数据生成（复用同批大纲，两个RQ可并行跑不同条件） |
| 第3周 | RQ2 + RQ3 数据生成；RQ1数据评估打分 |
| 第4周 | 全部评估打分完成；统计检验；初版图表 |
| 第5周 | 论文撰写：Method + Results 章节；内部审校 |
| 第6周 | Introduction/Related Work/Discussion 补全；投稿前 polish（对齐 ACL Findings 格式要求） |

---

## 6. 与原落地方案文档的对应关系

本研究方案直接复用原文档中的以下设计，未做训练相关改动：

- Story Orchestrator 六模块架构（State Manager / Retriever / Planner / Drafter / Reviser / Consistency Checker）
- story_state JSON schema（世界观、角色卡、plot_state、chapter_state）
- StoryJob 接口设计（Flowith/Manus 编排思路，可作为未来系统论文的落地部分，本次实证研究不依赖具体编排平台，直接用 API 调用模拟）
- 模型池与定价数据（GPT-4.1、Claude Sonnet 4.6、Gemini 2.5 Pro、DeepSeek-V4、GLM-5.1、Qwen3）
- 评估工具引用（StoryScope narratology checker、ConStory-style consistency checker、MAUVE、BERTScore）

原文档中涉及训练的部分（LoRA/QLoRA/SFT/DPO/RLHF、GPU选型）不在本研究范围内，留作后续论文的 Future Work 或独立的落地系统论文。
