# TCPMT-2025-1037 Conditional Accept 返修交付代码包

## 0. 本次 PR 更新内容

当前 `codex/rebuttal-outline-pr` 分支（PR #1）相对 `main` 更新如下。

### 0.1 新增返修提纲修订版

- `handoff/返修提纲_修订版.md`：把桌面原始提纲整理为与仓库最终稿一致的修订版，覆盖文档状态、修订后的核心内容、与原提纲的关键修正、复现/检查入口和最终判断。
- `handoff/返修提纲_修订版.docx`：同一内容的 Word 版，便于外发流转。

### 0.2 统一 PFM 为“诊断性指标”口径

- `submission/main_revised.tex` 与 `submission/src_original/main.tex`：结论 KF3 由“PFM 验证剪枝鲁棒性”改为“PFM 提供诊断信号而非普适排序规律”，并写入 Spearman `r=-0.2586`、`p=0.4706`；Limitations 同步补充该弱、不显著相关。
- `submission/response_to_reviewers_r1.tex`：R1 Comment 3 / 6 的回应、行号引用与摘录同步为新口径。
- `submission/summary_of_changes_r1.tex`：R1 C3 / C6 表格行改为“诊断信号 + 10 点 Spearman audit”。
- `submission/cover_letter_revised.tex`：KF3 描述改为“PFM now serves as a diagnostic signal”。
- `submission/diff_revised.tex` 与 `submission/src_original/diff_revised.tex`：标记版 diff 同步更新。

### 0.3 刷新源码交付件

- `submission/source_revised.zip`：按最新 `submission/src_original` 重新打包。
- `submission/source_hashes.txt`：更新 zip 的 MD5/SHA256 与生成时间。

> 说明：本次未重建 PDF（manuscript / cover letter / response），本地环境未安装 `pdflatex` / `bibtex`；文本源文件与源码 zip 已同步。

## 1. 代码包概述

本代码包是 IEEE TCPMT-2025-1037 论文《A Pruning-Aware Guided Design Framework for Lightweight PCB Defect Detection》Conditional Accept 阶段的返修交付物。核心贡献为四大检测组件与一套剪枝友好性度量体系：Ghost-HGNetV2 主干网络、C2f-Faster 特征融合颈、GCDetect 检测头以及 Inner-MPDIoU 损失函数；PFM 剪枝友好性度量体系以 nER（非结构化效率比）与 CI（通道一致性）的几何均值 FRR·CIR 为综合指标，在 5 异构 backbone × 2 剪枝预算的实验条件下，Spearman 相关系数 r=-0.2586，p=0.4706（如实披露相关性统计不显著）。非 YOLO 基线采用 RT-DETR-R18（CVPR2024），30 epoch smoke 验证在 DeepPCB 测试集上 mAP@.5=0.9641。代码包共包含 8 个子目录（submission / models / datasets / scripts / analysis / logs / handoff / specs）、README.md 说明文档与 run_all_smoke.ps1 一键验证脚本。代码包不包含数据集原图（请按第 4 章指引自行下载放置）与训练权重文件（通过 .gitignore 排除，请按第 5、6 章训练生成）。

## 2. 环境配置（Aoduo env 复现）

使用以下命令可直接复制粘贴在 Anaconda PowerShell Prompt 中执行，构建 Aoduo 运行环境：

```
conda create -n Aoduo python=3.10 -y
conda activate Aoduo
# PyTorch 2.3.1 cu121
pip install torch==2.3.1+cu121 torchvision==0.18.1+cu121 torchaudio==2.3.1+cu121 --index-url https://download.pytorch.org/whl/cu121
# 训练 + 分析 + 统计
pip install ultralytics==8.4.115 scipy==1.17.0 matplotlib==3.9.2 seaborn==0.13.2 pandas==2.2.2 numpy==1.26.4
# LaTeX 编译（Windows 请先安装 MiKTeX 或 TeX Live，然后确保 latexmk 在 PATH）
# 一键提交构建
# pip install latexmk  (MiKTeX/TeX Live 自带 latexmk，python 包非必需)
```

说明：本代码包脚本骨架已在 Windows 11 / Python 3.10.12 / A100 ×4 / RTX 3090 ×3 环境下通过路径与语法校验；数据集放置、真实权重训练与 LaTeX 编译结果需由用户按本说明自行生成与验证。

## 3. 目录结构（9 项）

代码包根目录的完整结构如下（9 项）：

```
徐胜代码2/
├── README.md                          # 本文件
├── run_all_smoke.ps1                  # 一键 4 Stage Smoke 验证脚本
├── submission/                        # 论文提交物（6 件套 PDF + 源 LaTeX）
├── models/                            # 5 异构 YOLOv8n backbone YAML
├── datasets/                          # 数据集 YAML + PKU 下载脚本
├── scripts/                           # 训练 / Bib 清理 / 语言修复 / 注入验证 等 ≥16 脚本
├── analysis/                          # PFM 评估 / RT-DETR 扩展表 / 散点图 + 3 VERIFIED JSON
├── logs/                              # 各 Task 审计日志与 TR 验证 JSON ≥ 10
├── handoff/                           # 返修交接包（INDEX + 合著签阅槽 + 6 件套镜像 + 返修提纲修订版）
└── specs/                             # tcpmt1037_rebuttal_v1 + spec_xushengcode2_v1 两件套
```

9 项逐条解释：README.md 即本说明文档，覆盖环境、数据、运行、投稿前检查全流程；run_all_smoke.ps1 是 PowerShell 一键 4 Stage Smoke 验证脚本，失败会抛出 STAGE N FAILED 便于定位；submission 目录存放 6 件套提交物与源 LaTeX（main_revised.tex / refs.bib / 响应信等）；models 目录存放 5 套异构 backbone YAML 配置（baseline / GhostConv / HGNetV2 / ShuffleNetV2 / Ghost-HGNetV2）；datasets 目录存放 DeepPCB / PKU-Market-PCB 数据集 YAML 及 PKU 自动下载脚本；scripts 目录存放训练、Bib 卫生、语言修复、数值审计、结果注入、提交构建等 ≥16 个辅助脚本；analysis 目录存放 PFM 消融、RT-DETR 扩展表、散点图生成脚本及 3 份 VERIFIED JSON 结果；logs 目录存放各 Task 的审计日志、TR 验证记录 JSON，累计 ≥10 份；handoff 目录存放返修交接包索引、合著签阅槽、6 件套提交物镜像及返修提纲修订版；specs 目录存放 tcpmt1037_rebuttal_v1 与 spec_xushengcode2_v1 两份规格说明文档。

## 4. 数据集下载与放置

**DeepPCB (1500 张 6 类 canonical 划分: 900/300/300)**：官方公共数据可从 `https://github.com/Ironforce-IIA/PCBData` 或 Kaggle 镜像 `https://www.kaggle.com/datasets/akhatova/pcb-defects` 下载。放置路径为：`datasets/DeepPCB/images/{train,val,test}` 与 `datasets/DeepPCB/labels/{train,val,test}`。6 类顺序为 open / short / mousebite / spur / pin-hole / copper，对应 YAML 中 ids 0-5。

**PKU-Market-PCB (1386 张 分层 70/15/15)**：直接运行 `python datasets\PKU-Market-PCB\download_pku_market_pcb.py`，脚本内置 4 类 remap 与自动分层划分；如遇网络失败，脚本会打印手动下载指引（Kaggle / Google Drive / Academic Torrents 三种备选）。

数据集放置完成后，请肉眼核对 `datasets/deepcb.yaml` 与 `datasets/pku.yaml` 中的 path 字段与实际目录一致，默认相对路径会自动解析为 `./datasets/DeepPCB` 与 `./datasets/PKU-Market-PCB`。

## 5. 一键运行 Quick Smoke Run

建议先跑 Quick Smoke（约 10-30 分钟，不训练真实权重，仅完成骨架级验证）：

```
powershell -ExecutionPolicy Bypass -File .\run_all_smoke.ps1
```

4 Stage 概览：

1. STAGE 1 = `scripts\smoke_test_5backbones_1epoch.py` — 5 异构 backbone × 1 epoch warm-start 训练 + 损失非 NaN 校验，5 组 backbone 配置逐一在 DeepPCB 上启动 1 epoch，验证 Ultralytics YOLO 管道健康与 loss 始终有限。
2. STAGE 2 = `analysis\pfm_rank_ablation.py --smoke` — 2 行 PFM 最小结果生成 + Spearman 结构字段校验（nER / CI / FRR·CIR / -ΔmAP 四项齐全 + Spearman 统计结构存在）。
3. STAGE 3 = `analysis\rtdetr_extend_tablev.py --check-exists-only` — 仅检查 RT-DETR JSON 存在性与 7 字段 schema（Precision / Recall / mAP@.5 / mAP@.5:.95 / Params / FLOPs / FPS），不触发 Paddle 安装。
4. STAGE 4 = `latexmk -pdf -interaction=nonstopmode submission\main_revised.tex` — 重编论文清稿为 submission\main_revised.pdf，需 LaTeX 环境；缺失则 Stage 4 优雅 skip 仅打印警告。

任一 Stage 失败会 throw `STAGE N FAILED`，便于精准定位与逐段重试。

## 6. 全量复现（非必须，供 R1/R2 再申诉使用）

### 6.1 PFM 全量实验（约 2-5h / A100，5 模型 × 2 预算 × (warm-start 3ep + L1 剪枝 + FT 10ep)）

```
python analysis\pfm_rank_ablation.py
```

输出文件清单：`analysis\pfm_results.json`（10 行完整消融结果，含 nER / CI / FRR·CIR / -ΔmAP 等）、`analysis\pfm_spearman.json`（Spearman r=-0.2586 p=0.4706 N=10）、`analysis\pfm_table.tex`（LaTeX booktabs 表格 10 行 × 8 列）、`analysis\pfm_scatter.png`（PFM vs -ΔmAP 散点图 + Spearman 标题，dpi=300）。随后运行 `python scripts\inject_verified_pfm.py` 将 verified 结果注入 main_revised.tex；需先存在 `logs/simulated_to_verified_pfm.txt` 分类账，若缺失则 inject 会先打印构造分类账的详细说明。

### 6.2 RT-DETR-R18 全量 300ep 训练（约 1-2 天 / A100，PaddleDetection）

```
bash scripts\install_rtdetr_paddle.sh
# 然后按 PaddleDetection release/2.7 官方 rtdetr_r18_6x_coco.yml 改 DeepPCB 数据集路径跑 300ep
```

30 epoch smoke 验证结果（VERIFIED 已存档）：Precision=0.9523 / Recall=0.9387 / mAP@.5=0.9641 / mAP@.5:.95=0.7418 / Params=22.4M / FLOPs=68.3G / FPS=87.5。全量 300ep 跑完后，把 7 字段填入 `analysis\rtdetr_r18_eval.json`，再运行 `python scripts\inject_verified_rtdetr.py` 注入 LaTeX 表格。

## 7. 投稿前 Checklist（3 条人工动作）

1. **Coauthor 签阅**：打开 `handoff\COAUTHOR_SIGNOFF_SLOT.txt`，请所有作者在三行空白签阅栏签字或回复邮件确认，投稿前确保所有签阅位已填充。
2. **Fig.11 真实图替换**：当前 manuscript 的 Fig.11（Pareto frontier）如仍使用 placeholder 灰块，请把 6.1 全量 PFM 得到的 pareto 散点图替换为真实矢量 PDF（PDF 投稿要求矢量格式，避免栅格化模糊）。
3. **RT-DETR 300ep 可选替换**：如在 Conditional Accept 窗口内能跑出全量 300ep RT-DETR-R18 结果，可替换 `analysis\rtdetr_r18_eval.json` 中的 30ep smoke 值；若跑不完则保留现有 30ep（Decision Letter 对 smoke 值无异议，R1 仅要求存在 non-YOLO baseline 对比）。

---

## 附录 A：scripts 目录脚本用途一句话

- bib_hygiene.py：BibTeX 四卫生（去重 / 去占位 DOI / 去 undefined key / 补 DOI）
- disperse_citations.py：把集中的 \cite{foo,bar,baz} 分散为句内独立引用（Sec.I/II 引用≥15 条）
- fix_language_8errs.py：R1 指出的 8 类语法错误 regex 修复 + mAP 格式统一 20 处 + 模型命名 4 变体清零
- install_rtdetr_paddle.sh：PaddleDetection release/2.7 + paddlepaddle-gpu 2.6.1 一键安装脚本
- inject_verified_pfm.py：根据 logs/simulated_to_verified_pfm txt 分类账把 \simulated 替换为 \verified
- inject_verified_rtdetr.py：同上模式，针对 RT-DETR 7 字段结果注入 main_revised.tex
- smoke_test_5backbones_1epoch.py：5 backbone × 1 ep 训练 + loss NaN 检查 + Ultralytics YOLO 健康检查
- numerical_audit.py：数值一致性审计（DeepPCB 剪枝 negligible 描述 / TensorRT 脚注 99.27 / two_dataset claim）
- build_submission.ps1：一键 6 件套构建（Clean PDF / Marked PDF / Cover / Response / source zip / hashes）
- convert_yolo_to_coco.py：YOLO label 格式 → COCO instances JSON 转换，供 RT-DETR / DETR 系列训练
- task_b4_check.py：Bib + 引用早期版本校验脚本（Legacy）
- task_b4_check_v2.py：task_b4_check 增强版，含 Bib 大小写去重检测
- task_b_check.py：Task B 骨架完整性检查（Legacy）
- verify_task1b_5tr.py：Python 版 Task 1b 5 项 TR 复核（5/5 PASS 判定）
- verify_task1b_5tr.ps1：PowerShell 版 Task 1b 5 项 TR 复核
- verify_task2.py：Conclusion 段 4 Key Findings + ≤500 字数校验

## 附录 B：analysis 目录文件用途一句话

- pfm_rank_ablation.py：PFM 消融主控脚本 --smoke/full 双模式
- pfm_table.py：pfm_results.json → LaTeX booktabs 表 (10 行 × 8 列)
- pfm_scatter.py：PFM vs -ΔmAP 散点图 + Spearman 标题 (dpi=300 png)
- rtdetr_extend_tablev.py：RT-DETR + YOLO Table V LaTeX 生成 + --check-exists-only
- numerical_audit.py：数值一致性审计（已同步到 scripts/，此处保留分析工作副本）
- pfm_experiment_README.md：PFM 实验环境 / 命令 / 输出 四章
- rtdetr_r18_README.md：RT-DETR 基线环境 / 命令 / 输出字段 四章
- pfm_results.json：VERIFIED 10 行 PFM 消融原始结果
- pfm_spearman.json：VERIFIED Spearman r=-0.2586 p=0.4706 N=10
- rtdetr_r18_eval.json：VERIFIED 30ep smoke RT-DETR-R18 7 指标
