# -*- coding: utf-8 -*-
"""根据密封的盲测映射文件，生成匿名编号A/B/C的合并文本文件（ch1+ch2拼接），
供后续“盲评”阶段阅读。此脚本本身不向控制台打印映射内容，避免评审者（本agent）
在阅读匿名文本前意外看到条件对应关系。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
EVAL_DIR = Path(__file__).resolve().parent

with open(EVAL_DIR / "blind_mapping_SECRET.json", "r", encoding="utf-8") as f:
    mapping = json.load(f)

PATHS = {
    "human_simulated": ["human_simulated/ch1.txt", "human_simulated/ch2.txt"],
    "ai_draft": ["ai_draft/ch1.txt", "ai_draft/ch2.txt"],
    "ai_revised": ["ai_revised/ch1.txt", "ai_revised/ch2.txt"],
}

for label, condition in mapping.items():
    parts = []
    for rel in PATHS[condition]:
        parts.append((BASE / rel).read_text(encoding="utf-8"))
    combined = "\n\n----（章节分隔）----\n\n".join(parts)
    out_path = EVAL_DIR / f"blind_text_{label}.txt"
    out_path.write_text(combined, encoding="utf-8")

print("匿名文本已生成：blind_text_A.txt / blind_text_B.txt / blind_text_C.txt（未打印对应关系）")
