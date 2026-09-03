# -*- coding: utf-8 -*-
"""生成盲测随机映射：把三个条件随机打乱编号为A/B/C，写入密封文件。
仅本脚本运行时知道映射，随后在“盲评”阶段假装不知道这个映射，仅基于文本内容判断。
"""
import random
import json

random.seed()
conditions = ["human_simulated", "ai_draft", "ai_revised"]
labels = ["A", "B", "C"]
random.shuffle(conditions)
mapping = dict(zip(labels, conditions))

with open("blind_mapping_SECRET.json", "w", encoding="utf-8") as f:
    json.dump(mapping, f, ensure_ascii=False, indent=2)

print(json.dumps(mapping, ensure_ascii=False, indent=2))
