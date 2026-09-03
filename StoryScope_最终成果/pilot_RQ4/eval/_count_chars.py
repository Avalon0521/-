# -*- coding: utf-8 -*-
import os

def count(path):
    with open(path, encoding='utf-8') as f:
        text = f.read()
    chars = len(text.replace('\n', ''))
    return chars, len(text)

files = [
    'strategy_A_allstrong/ch1.txt',
    'strategy_A_allstrong/ch2.txt',
    'strategy_B_allcheap/ch1.txt',
    'strategy_B_allcheap/ch2.txt',
    'strategy_C_router/ch1/draft_by_cheap.txt',
    'strategy_C_router/ch1/final_after_strong_revise.txt',
    'strategy_C_router/ch2/draft_by_cheap.txt',
    'strategy_C_router/ch2/final_after_strong_revise.txt',
    'master_ground_truth.json',
]

base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for f in files:
    p = os.path.join(base, f)
    c, l = count(p)
    print(f, c, l)
