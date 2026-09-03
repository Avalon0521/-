# StoryScope 视角下的 AI 小说系统研究方案 —— 最终成果整理

## 本文件夹内容

| 路径 | 说明 |
|---|---|
| `StoryScope_研究方案与论文撰写草稿.md` | **最终研究方案**：5 个可用 API 计算实验验证的研究问题（RQ1-RQ5）、共享实验基础设施、预算估算、人工评估协议、论文撰写骨架（含 Limitations / Ethics 独立章节）。全部实验仅调用商用 LLM/Embedding API，不训练模型。 |
| `审稿反馈/01_实验严谨性审稿(RQ1-4).txt` | 第一轮审稿：聚焦 RQ1-4 的实验设计严谨性问题（judge 自我偏好偏差、RQ3 循环论证风险、样本量与统计功效、跨 RQ 独立性）。 |
| `审稿反馈/02_新颖性审稿.txt` | 第二轮审稿：聚焦本文相对 StoryScope（CCF-A 原文）的新颖性与因果延续关系，提出补充人类锚定评估（即最终方案中的 RQ5）。 |
| `审稿反馈/03_论文结构与Venue适配审稿.txt` | 第三轮审稿：聚焦投稿 ACL/EMNLP Findings 的结构完整性（Limitations、Ethics Statement、人工评估协议、Related Work 中与 StoryScope 关系的说明、agentic 写作系统文献空白）。 |

## 三轮审稿分别改了什么（可对照 diff 追溯）

1. **严谨性审稿 → 方法论修正**：judge 模型改为与被评测 drafter/reviser 池完全不重叠的独立 judge（o系列）+ 交叉验证 judge，报告 judge 间一致性；RQ3 新增"自改"对照组以区分"趋同于 reviser 风格"与"指纹被真正削弱"两种机制；样本量小的检验（RQ4 非劣效检验、RQ3 分类准确率）改为报告效应量与置信区间而非仅 p 值，并在文中明确标注为描述性趋势；新增 3.6 节讨论跨 RQ（RQ1/RQ2/RQ4 复用同批草稿）的独立性与多重比较问题。

2. **新颖性审稿 → 新增 RQ5**：原方案的 RQ1-RQ4 全部是"AI vs AI"内部比较，未回答"这套生成流水线相对 StoryScope 已验证的人机可分性基线（93.2% vs 68.4% macro-F1）到底缩小了多少 gap"这一核心问题。新增 RQ5（人类锚定的盲测图灵测试），引入人类语料对照 + StoryScope 检测器探针 + 小规模人工盲测，把四个孤立的工程对比统一为"生成-检测军备竞赛"叙事，与 CCF-A 原文形成因果延续关系。

3. **结构审稿 → 补全投稿必需章节**：新增独立的 Limitations 章节（judge-human 一致性未大规模验证、题材/语言泛化性、模型版本漂移、小样本统计功效、检测器自身偏差）；新增 Ethics/Broader Impact 声明（版权与训练语料、生成内容滥用风险、对人类作者劳动市场的潜在影响）；将人工评估从"若资源允许"占位改为具体协议（每 RQ 20-30 篇、双标注、Kappa 一致性、第三方仲裁）；Related Work 补充 agentic 多智能体写作系统文献（Re3、DOC 等）并新增段落明确本文与 StoryScope/ConStory-Bench 的"工具提出 vs 工具应用于机制研究"关系；Introduction 结尾新增统一框架句，避免被读成多篇 workshop paper 拼接。

## 原始输入文件（未移动，供追溯）

- `../StoryScope视角下的AI小说系统研究与落地方案.pdf` —— 原始落地方案文档
- `../storyscope_extracted.txt` —— 从 PDF 提取的文本
- `../.aris_review/` —— 三轮审稿的原始输出（含精简版 review*.txt 与完整版 review*_full.txt），本文件夹中的审稿反馈为完整版的复制件

## 后续工作（占位，需人工补全）

见 `StoryScope_研究方案与论文撰写草稿.md` 第 4 节"需要人工补全的部分"：实验结果数值与图表、标注者招募确认、Related Work 具体 BibTeX 引用、数据/代码发布计划（Reproducibility Checklist）。
