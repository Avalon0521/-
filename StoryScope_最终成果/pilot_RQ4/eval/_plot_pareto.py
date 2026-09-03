# -*- coding: utf-8 -*-
"""
生成RQ4 pilot 成本-质量散点图（辅助可视化，非核心分析产出）。
数据来源：cost_estimates.json 的 summary.total_cost_usd 与 scores.json 的
narrative_quality_subjective_1to5（人工评分，1-5分）。
n=1（每种策略仅1次模拟运行），此图仅用于流程可行性演示，不构成统计意义上的帕累托前沿证据。
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

base = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(base, "cost_estimates.json"), "r", encoding="utf-8") as f:
    costs = json.load(f)

with open(os.path.join(base, "scores.json"), "r", encoding="utf-8") as f:
    scores = json.load(f)

points = [
    ("A_allstrong", costs["strategies"]["strategy_A_allstrong"]["summary"]["total_cost_usd"],
     scores["strategy_A_allstrong"]["aggregate"]["narrative_quality_subjective_1to5"], "tab:red"),
    ("B_allcheap", costs["strategies"]["strategy_B_allcheap"]["summary"]["total_cost_usd"],
     scores["strategy_B_allcheap"]["aggregate"]["narrative_quality_subjective_1to5"], "tab:blue"),
    ("C_router", costs["strategies"]["strategy_C_router"]["summary"]["total_cost_usd"],
     scores["strategy_C_router"]["aggregate"]["narrative_quality_subjective_1to5"], "tab:green"),
]

fig, ax = plt.subplots(figsize=(6, 5))
for name, cost, quality, color in points:
    ax.scatter(cost, quality, s=140, color=color, label=name, zorder=3)
    ax.annotate(name, (cost, quality), textcoords="offset points", xytext=(8, 6), fontsize=9)

ax.set_xlabel("模拟总成本估算 (USD, 2章合计, 按公开定价量级估算)")
ax.set_ylabel("叙事质量主观分 (1-5, 人工评分)")
ax.set_title("RQ4 Pilot: 成本-质量关系 (n=1 每策略, 流程可行性演示)")
ax.set_ylim(0, 5.5)
ax.grid(True, linestyle="--", alpha=0.4)
ax.legend(loc="lower right")

fig.tight_layout()
fig.savefig(os.path.join(base, "cost_quality_scatter.png"), dpi=150)
print("saved cost_quality_scatter.png")
