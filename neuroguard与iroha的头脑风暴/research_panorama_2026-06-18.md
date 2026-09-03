# 论文调研全景与研究 idea 初筛

日期: 2026-06-18  
输入论文:

- `988_NeuroGuard_Cross_Modal_Bin.pdf`
- `4490_IROHA_Three_Phase_Gradual.pdf`

## 0. 执行记录

- 已按要求在 GitHub 上查找 Codex skills。curated 列表中与本任务最相关的是 `pdf` skill；experimental 路径当时不可用。
- 已从 `openai/skills` 安装 `pdf` skill 到本机 Codex skills 目录。安装后需要重启 Codex 才会自动出现在技能列表中。
- 已用本地 `pypdf` 提取两篇 PDF 的正文，用联网检索补充截至 2026-06-18 的相关论文。

## 1. 一句话结论

更值得优先推进的是 NeuroGuard 方向的后续工作: **API-only 的状态化跨模态安全守卫，面向 multi-turn first-unsafe-turn 检测**。原因是当前 MLLM safety 已经从单轮 jailbreak/SIUO 进入多轮上下文风险阶段，2026 年 MTMCS-Bench 已经证明现有 guardrails 仍不能完全解决多轮 contextual safety；而 NeuroGuard 的最大部署痛点是需要 hidden-state access。把 NeuroGuard 的 first-unsafe-turn 指标和状态化思想迁移到 API-only/black-box 场景，有明确缺口、算力成本低、可快速验证。

IROHA 方向也有可做点，但 3DGS compression 在 2024-2026 年非常拥挤，最新工作已经走向 target-size、joint pruning + quantization + entropy coding、memory-bounded training。单纯改 pruning schedule 的新颖性压力较大，除非把 IROHA 明确升级成 rate-distortion/VRAM constrained controller。

## 2. 两篇 PDF 的定位

### 2.1 NeuroGuard

主题: MLLM safety, SIUO, cross-modal binding anomaly detection, inference-time guardrail。

核心 claim:

- 单轮 SIUO 风格 benchmark 在若干 frozen feature 上已接近饱和，论文报告 NeuroGuard 和 flat MLP 都能到 AUC=1.0。
- 真正贡献不在再刷单轮 AUC，而在部署压力: boundary mixup、多轮 gradual escalation、zigzag PGD、subspace replacement、latency cascade。
- 方法是 4 层轻量 monitor: complexity estimation、gated recurrent filter、multi-scale angular consistency/MAC + cumulative deviation/CDS、logistic fusion。
- 重要限制: 新型 compositional risk 仍可能需要 recalibration；长会话可能需要 reset；更广 backbone 需要 hidden-state access。

对后续研究的启发:

- 单轮分类已经不是最好的战场。
- 多轮 first-unsafe-turn、false alarm before unsafe turn、utility-preserving detection 是更有价值的指标。
- hidden-state access 是现实部署门槛，尤其对闭源 API 模型。

### 2.2 IROHA

主题: 3D Gaussian Splatting compression, gradual pruning, recovery-aware schedule。

核心 claim:

- 把 3DGS pruning 拆成三阶段: 先几何学习，再冻结 densification 后渐进 percentile pruning，最后 post-pruning recovery。
- 论文主张 schedule/recovery dynamics 比复杂 importance score 更关键，简单 opacity proxy 也能有不错表现。
- 在 NeRF Synthetic 上报告减少约 40% Gaussian 且质量持平或略升；量化后达到约 5.5x 总压缩。
- 重要限制: 激进 5%-8% pruning 会造成 3-4 dB drop；Mip-NeRF 360 个别真实场景仍掉点；kitchen eval path 有异常说明；完整真实场景 secondary metrics 仍未完全覆盖。

对后续研究的启发:

- IROHA 的价值在 schedule/control，而不是新的 score。
- 需要把 schedule 和 target size、mixed precision、scene difficulty、peak VRAM 约束合起来，否则容易被 2026 的 joint compression 工作压过。

## 3. 最新文献地图

### 3.1 MLLM safety / guardrails

近期脉络:

- 早期攻击与 benchmark 关注 image jailbreak、typographic prompt、VSIL/SIUO 等单轮输入。代表包括 [FigStep](https://arxiv.org/abs/2311.05608)、[MM-SafetyBench](https://arxiv.org/abs/2311.17600)、[VLSBench](https://arxiv.org/abs/2411.19939)。
- 2024-2025 年出现更系统的 safety evaluation suite 和 guardrail: [MLLMGuard](https://arxiv.org/abs/2406.07594)、[SafeBench](https://arxiv.org/abs/2410.18927)、[UniGuard](https://arxiv.org/abs/2411.01703)、[LlavaGuard](https://arxiv.org/abs/2406.05113)、[OMNIGUARD](https://arxiv.org/abs/2505.23856)。
- 2025-2026 年开始强调动态、上下文、多轮和具身场景: [SDEval](https://arxiv.org/abs/2508.06142) 用 text/image/text-image dynamics 生成动态安全评估；[MTMCS-Bench](https://arxiv.org/abs/2601.06757) 直接评估多轮 multimodal contextual safety；[GuardAlign](https://arxiv.org/abs/2602.24027) 做 test-time safety alignment；[SafetyALFRED](https://arxiv.org/abs/2604.19638) 把安全从 QA 推到 embodied planning。

反复出现的局限:

- 单轮 benchmark 容易饱和或被数据污染。
- 视觉风险和文本风险常被分开处理，真正的 cross-modal intent 没有被稳定建模。
- 多轮风险会逐步显现，guardrail 要么漏掉 gradual escalation，要么过度拒绝 benign dialogue。
- 很多强方法需要内部表示、attention 或 hidden states，闭源 API 部署困难。
- 自动评测常依赖 LLM judge，存在评估偏差和 policy 边界不一致。

### 3.2 3DGS compression / pruning

近期脉络:

- 3DGS 原始方法见 [3D Gaussian Splatting for Real-Time Radiance Field Rendering](https://arxiv.org/abs/2308.04079)，它带来实时 novel-view synthesis，但 Gaussian 数量和属性存储成为瓶颈。
- 2023-2024 的压缩/剪枝代表包括 [LightGaussian](https://arxiv.org/abs/2311.17245)、[Compact 3D Gaussian Representation](https://arxiv.org/abs/2311.13681)、[Mini-Splatting](https://arxiv.org/abs/2403.14166)、[HAC](https://arxiv.org/abs/2403.14530)、[F-3DGS](https://arxiv.org/abs/2405.17083)。
- 综述类工作包括 [3DGS.zip](https://arxiv.org/abs/2407.09510) 和 [Compression in 3D Gaussian Splatting](https://arxiv.org/abs/2502.19457)。
- 2024-2026 的趋势是 target size、mixed precision、joint pruning/quantization、peak memory control。代表包括 [SizeGS](https://arxiv.org/abs/2412.05808)、[MEGS^2](https://arxiv.org/abs/2509.07021)、[GETA-3DGS](https://arxiv.org/abs/2605.02086)、[MesonGS++](https://arxiv.org/abs/2604.26799)、[Gaussians on a Diet](https://arxiv.org/abs/2604.20046)。

反复出现的局限:

- 手调 opacity threshold、固定 prune ratio、固定 bit width 跨场景泛化弱。
- PSNR/SSIM/LPIPS 与真实视觉缺陷、thin structures、occlusion boundaries 的关系不稳定。
- 存储压缩、训练峰值显存、渲染显存、FPS 往往被分开优化。
- 很多方法在不同 codebase、不同 eval protocol 下比较，Pareto 位置不清。
- 真实场景和 unbounded scenes 比 synthetic scenes 更容易暴露失败。

## 4. 开放问题

### 4.1 MLLM safety

1. 如何定义并检测 first unsafe turn，而不是只判断最终回答是否 unsafe。
2. 如何在 API-only/black-box 场景近似 NeuroGuard 的 cross-modal binding signal。
3. 如何在多轮对话中区分 benign context switch 和 malicious gradual escalation。
4. 如何降低 false alarm before unsafe turn，保持 helpfulness。
5. 如何构造不容易被 benchmark overfitting 的动态安全样本。
6. 如何评测 guardrail 的 latency/cost/safety/utility Pareto，而不是只看 ASR 或 F1。

### 4.2 3DGS compression

1. 如何把 IROHA 的 recovery-aware schedule 变成 target-size 或 target-VRAM controller。
2. 如何识别 thin structures、occlusion boundaries、view-dependent regions 等几何敏感区域。
3. 如何把 pruning、quantization、entropy coding 放进统一 rate-distortion loop。
4. 如何用少量 probe views 预测继续剪枝会不会造成局部不可恢复损伤。
5. 如何建立统一 codebase/protocol，公平比较 schedule-only、score-based 和 codec-based 方法。

## 5. 10 个具体 idea 初筛

| # | Idea | 方向 | 快速查新判断 | 可行性 | 算力/成本 | 初筛结论 |
|---|---|---|---|---|---|---|
| 1 | API-only Stateful Cross-Modal Intent Ledger: 用 caption/OCR/object-affordance/text-risk/response-risk 构建多轮风险账本，输出 first unsafe turn 和 block/defer/pass | MLLM safety | MTMCS-Bench 已覆盖多轮 contextual safety，但未见明确 API-only 状态化 cross-modal ledger guard；NeuroGuard 需要 hidden states | 高 | 低-中，API 或 1-2 张消费级 GPU 即可 | Top idea |
| 2 | Hidden-state-free NeuroGuard distillation: 用可观测输入输出特征蒸馏 NeuroGuard 的 MAC/CDS 风格分数 | MLLM safety | 和 NeuroGuard 差异明确，但需要 NeuroGuard/open MLLM 作为 teacher | 中 | 中，需要跑 open MLLM hidden states 和生成数据 | 可做为 #1 的增强 |
| 3 | Dynamic SIUO generator: 用 SDEval 风格 text-image dynamics 自动生成新的 SIUO/OOD compositional risks | MLLM safety | SDEval 已有动态评估，单独做 generator 新颖性一般 | 高 | 低-中 | 适合做数据增强模块 |
| 4 | Long-session reset policy for stateful guards: 学习何时遗忘/重置 CDS，降低长会话 false positives | MLLM safety | NeuroGuard 自述长会话可能需要 reset；公开工作较少 | 中 | 低 | 小而清楚，可并入 #1 |
| 5 | Guard cascade optimizer: 在 LlavaGuard/UniGuard/OMNIGUARD/LLM judge 之间学习何时转发，优化 latency-safety-utility | MLLM safety | 级联思想常见，NeuroGuard 也做 cascade；创新要靠 cost-aware policy | 高 | 低-中 | 工程价值高，论文风险中 |
| 6 | Rate-Distortion IROHA: 把三阶段 pruning schedule 改成目标 size/PSNR 控制器 | 3DGS | SizeGS/GETA/MesonGS++ 已强相关；需突出 recovery-aware schedule | 中 | 中，高质量实验需多场景 GPU | Runner-up |
| 7 | Geometry-sensitive IROHA: 加 thin-structure/occlusion boundary risk score，防止真实场景局部崩坏 | 3DGS | 很多 importance score 已存在，但和 recovery schedule 结合仍有空间 | 中 | 中 | 适合做 ablation-rich 工作 |
| 8 | Memory-bounded IROHA: 在训练峰值显存约束下交替 grow/prune/recover | 3DGS | Gaussians on a Diet 已非常接近，需谨慎 | 中 | 中 | 新颖性压力大 |
| 9 | Probe-view early warning: 用少量 held-out/probe views 预测下一轮 pruning 的不可恢复风险 | 3DGS | 未见完全同名，但和 active validation/importance 相关 | 中 | 中 | 可作为 #6/#7 子模块 |
| 10 | Unified benchmark harness for 3DGS pruning schedules: 复现 IROHA/LightGaussian/Mini-Splatting/GETA 子集，统一 protocol | 3DGS | 综述有统一标准诉求，但 harness 本身偏系统/benchmark | 高 | 中-高 | 对投稿不一定够，但对研究非常实用 |

## 6. Top idea 深度验证

### 6.1 推荐题目

**SCIL-Guard: API-only Stateful Cross-Modal Intent Ledger for Multi-Turn MLLM Safety**

中文名: API-only 状态化跨模态意图账本守卫。

核心问题:

> 在不能访问 hidden states 的闭源或托管 MLLM 场景中，能否用可观测输入、轻量视觉解析、文本风险、跨轮状态和反事实提示，提前检测 first unsafe turn，同时保持 benign multi-turn dialogue 的 helpfulness?

### 6.2 方法草图

每轮输入为图像、用户文本、历史对话。SCIL-Guard 在目标 MLLM 前面运行:

1. Perception layer: 用轻量 VLM/OCR/caption/object detector 得到对象、动作、可供性、危险物、文字图像内容。
2. Intent hypothesis layer: 生成 benign goal 和 risky goal 两套解释，比较二者与历史上下文的匹配。
3. Cross-modal binding features: 计算图像对象与文本动作/意图的绑定风险，例如工具-动作、对象-受害者、地点-行为、文本隐喻与视觉 affordance。
4. Stateful ledger: 维护 risk budget、benign commitments、unresolved hazardous affordances、context switch score、escalation slope。
5. Decision layer: 输出 pass/defer/block，并给出 first-unsafe-turn score。defer 可转发给更贵的 response-level guard 或 human review。

### 6.3 和现有工作的差异

- 对 NeuroGuard: 保留 first-unsafe-turn、FApre/EarlyDR、stateful monitoring 思想，但不要求 hidden-state access。代价是信号更弱，因此需要更强的可解释账本和 cascade。
- 对 MTMCS-Bench: MTMCS-Bench 是多轮 contextual safety benchmark，并评估了现有 guardrails 仍有缺口；SCIL-Guard 是面向该缺口的方法。
- 对 GuardAlign: GuardAlign 是 test-time alignment，使用 safety detection 和 attention calibration；SCIL-Guard 不改目标模型内部生成过程，适合 API-only。
- 对 OMNIGUARD/UniGuard: 它们是强 guardrail baseline；SCIL-Guard 的差异是 conversation-level state、first-unsafe-turn objective、API-only observable feature design。
- 对 SDEval: SDEval 可作为动态评测和数据增强来源，而不是直接竞争方法。

### 6.4 完整查新结论

已检索关键词包括:

- `stateful multimodal guardrail MLLM`
- `API-only multimodal guardrail`
- `black-box stateful guardrail MLLM`
- `multi-turn multimodal large language models safety benchmark`
- `contextual safety multimodal large language models multi-turn dialogues`
- `output-level multimodal guardrail multi-turn`
- `safe prefix unsafe trajectory multimodal guardrail`

检索到最接近的工作:

- [MTMCS-Bench](https://arxiv.org/abs/2601.06757): 已经覆盖多轮 contextual safety，包含 escalation-based risk 和 context-switch risk，并指出现有 guardrails 不能完全解决。
- [GuardAlign](https://arxiv.org/abs/2602.24027): test-time safety alignment，降低 unsafe response，但不是 API-only 状态化 ledger。
- [OMNIGUARD](https://arxiv.org/abs/2505.23856): across languages/modalities 的 harmful prompt classifier，强调内部 aligned representations 和效率。
- [UniGuard](https://arxiv.org/abs/2411.01703): universal guardrail，考虑 unimodal 和 cross-modal harmful signals。
- [SDEval](https://arxiv.org/abs/2508.06142): 动态安全评估框架，可用于生成扰动样本。
- [MLLMGuard](https://arxiv.org/abs/2406.07594)、[SafeBench](https://arxiv.org/abs/2410.18927)、[VLSBench](https://arxiv.org/abs/2411.19939): evaluation suite/benchmark，而非 API-only stateful method。

判断:

- **benchmark-only 版本不建议做**，因为 MTMCS-Bench 已经非常接近。
- **method + metric + open evaluation harness 版本值得做**，特别是明确限定 API-only/no hidden states，并把 first-unsafe-turn、FApre、helpfulness、latency/cost 放进同一个 protocol。
- 新颖性最关键的防线是: 不是又一个静态 safety classifier，而是可解释的 conversation-level cross-modal state machine。

### 6.5 快速实验方案

最小可行版本:

- 数据: MTMCS-Bench、VLSBench、MM-SafetyBench、FigStep、COCO benign controls。若 SIUO 数据可获得，也加入。
- Baselines: prompted GPT-4o/Gemini judge、LlavaGuard、UniGuard、OMNIGUARD、简单 text-only risk classifier、caption+text risk classifier。
- Metrics: first-unsafe-turn F1、DR@T、FApre/EarlyDR、benign helpfulness/pass-through、latency、API cost。
- Ablations: no state、no visual affordance、no counterfactual benign/risky hypothesis、no reset、cheap-only vs cascade。
- 成功标准: 在 MTMCS-style paired dialogues 上，比 caption+text classifier 和 prompted judge 显著降低 FApre，同时提高 escalation/context-switch 检测；成本低于全量 response-level judge cascade。

算力估计:

- Prototype: 主要是 API 调用和缓存，低成本。
- 本地开源验证: 1 张 24GB GPU 可跑量化 VLM/LLM baseline；更系统实验建议 1-2 张 48GB/80GB GPU。
- 不需要训练目标 MLLM；最多训练 logistic regression/LightGBM/small transformer over features。

### 6.6 Devil's advocate review

最强反对意见:

1. MTMCS-Bench 已经提出多轮 contextual safety，SCIL-Guard 可能被认为只是一个工程 cascade。
2. API-only 特征可能太弱，遇到隐蔽视觉编码、OCR 噪声、抽象隐喻和 adversarial image 时会输给 hidden-state 方法。
3. 账本式状态容易 over-refuse。多轮中许多 benign context switch 看起来也像 risk accumulation。
4. 如果用 LLM 生成 hypothesis 和评测，又会出现 self-judging、policy drift 和不可复现问题。
5. 守卫的安全 policy 边界难统一，不同模型/地区/平台的拒答标准不同。
6. Latency 可能不如想象中低。每轮 caption/OCR/VLM judge 都可能吞掉部署优势。

如何化解:

- 把贡献限定在 API-only black-box setting，明确与 hidden-state guard 不在同一假设下竞争。
- 设计 deterministic feature path: OCR/object/caption/risk taxonomy 尽量可缓存、可复现，LLM hypothesis 只作为可选模块。
- 主指标必须同时包含 FApre 和 helpfulness，不能只追求 unsafe recall。
- 做 paired counterfactual evaluation: 同一图像、相似历史，一个 benign 一个 unsafe，证明不是简单看到危险物就拒绝。
- 给出 cost-aware cascade: cheap ledger 先跑，仅对高不确定样本调用昂贵 judge。
- 用 human-labeled subset 校验 LLM judge，避免评测循环。

Go/no-go:

- Go: 如果在 MTMCS-Bench 的 guardrail gap 上，SCIL-Guard 能以明显更低成本改善 first-unsafe-turn F1 和 FApre。
- No-go: 如果 caption+text prompted judge 或现成 UniGuard/OMNIGUARD 在同一 protocol 下已经接近上限，SCIL-Guard 只能提供解释而无性能或成本优势。

## 7. Runner-up: 3DGS 方向怎么做才不拥挤

推荐把 IROHA 扩展成:

**RDIROHA: Rate-Distortion and Memory-Aware Recovery Scheduling for 3D Gaussian Splatting**

不要只做新的 prune score。更稳的贡献组合是:

- target file size / target VRAM / target FPS 三种约束输入；
- recovery-aware gradual pruning 作为控制器；
- 少量 probe views 作为 irreversible damage warning；
- mixed precision/quantization 作为后处理或 joint stage；
- 统一对比 IROHA、LightGaussian、Mini-Splatting、SizeGS、GETA/MesonGS++ 可复现子集。

风险:

- GETA-3DGS、MesonGS++、SizeGS 已经覆盖 target-size 和 joint compression，很容易撞题。
- 实验成本明显高于 safety top idea。
- 若只在 NeRF Synthetic 上提升，很难有说服力；必须拿 Mip-NeRF 360/Tanks and Temples 的真实场景说话。

## 8. 建议下一步

优先路线:

1. 先做 SCIL-Guard 的 1 周 prototype: feature extraction + ledger + logistic/GBDT decision。
2. 用 MTMCS-Bench 和 VLSBench 的公开样本跑小规模验证。
3. 若结果显示现成 guardrail 已经足够强，及时转向 #2 hidden-state-free NeuroGuard distillation 或 #6 RDIROHA。

最低发表形态:

- 一个明确任务定义: API-only multi-turn cross-modal safety guard。
- 一个可复现方法: stateful intent ledger + cost-aware cascade。
- 一个评测协议: first-unsafe-turn、FApre、helpfulness、latency/cost。
- 一个强反方实验: 与 MTMCS-Bench 中的 guardrails、OMNIGUARD、UniGuard、prompted judge 对比。

## 9. 参考链接

MLLM safety:

- FigStep: https://arxiv.org/abs/2311.05608
- MM-SafetyBench: https://arxiv.org/abs/2311.17600
- LlavaGuard: https://arxiv.org/abs/2406.05113
- MLLMGuard: https://arxiv.org/abs/2406.07594
- SafeBench: https://arxiv.org/abs/2410.18927
- UniGuard: https://arxiv.org/abs/2411.01703
- VLSBench: https://arxiv.org/abs/2411.19939
- OMNIGUARD: https://arxiv.org/abs/2505.23856
- SDEval: https://arxiv.org/abs/2508.06142
- MTMCS-Bench: https://arxiv.org/abs/2601.06757
- GuardAlign: https://arxiv.org/abs/2602.24027
- SafetyALFRED: https://arxiv.org/abs/2604.19638

3DGS:

- 3D Gaussian Splatting: https://arxiv.org/abs/2308.04079
- LightGaussian: https://arxiv.org/abs/2311.17245
- Compact 3D Gaussian Representation: https://arxiv.org/abs/2311.13681
- Mini-Splatting: https://arxiv.org/abs/2403.14166
- HAC: https://arxiv.org/abs/2403.14530
- F-3DGS: https://arxiv.org/abs/2405.17083
- 3DGS.zip survey: https://arxiv.org/abs/2407.09510
- SizeGS: https://arxiv.org/abs/2412.05808
- Compression in 3D Gaussian Splatting survey: https://arxiv.org/abs/2502.19457
- MEGS^2: https://arxiv.org/abs/2509.07021
- MesonGS++: https://arxiv.org/abs/2604.26799
- Gaussians on a Diet: https://arxiv.org/abs/2604.20046
- GETA-3DGS: https://arxiv.org/abs/2605.02086
