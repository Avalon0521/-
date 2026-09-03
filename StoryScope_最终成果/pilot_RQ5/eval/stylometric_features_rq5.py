# -*- coding: utf-8 -*-
"""
RQ5 pilot：纯标准库（re + collections + math）实现的文本统计特征代理指标，
扩展自 pilot_RQ3/eval/stylometric_features.py。

【极其重要的诚实声明，务必先读】
本脚本计算的一切数字都只是手工挑选的表层文本统计特征（字符/bigram distinct ratio、
平均句长、标点密度、虚词/动词分布）之间的欧氏距离/余弦相似度，以及几个手工列出的
“AI套话”短语的密度——这不是、也不能替代：
  (a) 真实的 embedding 语义可分性检验（无 embedding API）；
  (b) 真实的 StoryScope 304类检测器（未调用、未复现）；
  (c) 任何经过训练/校准的机器学习分类器（本脚本没有训练任何模型，只是规则/密度统计）。
所有输出仅可用于验证“统计代理指标计算流程是否可执行”，其数字的方向性观察
（见 RQ5_pilot_summary.md）不构成有统计效力的证据。

用法：python stylometric_features_rq5.py
输出：
  - 三个条件（human_simulated / ai_draft / ai_revised）的原始特征
  - 两两欧氏距离矩阵（z-score标准化）与余弦相似度矩阵
  - AI套话短语密度（每100字），作为第二个独立的、更直接的“AI-ness”表层代理信号
  - 综合方向性摘要：ai_draft 和 ai_revised 谁在统计特征空间中离 human_simulated 更近
"""
import re
import math
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CONDITIONS = {
    "human_simulated": ["human_simulated/ch1.txt", "human_simulated/ch2.txt"],
    "ai_draft": ["ai_draft/ch1.txt", "ai_draft/ch2.txt"],
    "ai_revised": ["ai_revised/ch1.txt", "ai_revised/ch2.txt"],
}

# 与 RQ3 相同的固定虚词/语气词表，保持方法一致、可横向比较
FUNCTION_WORDS = [
    "了", "的", "着", "就", "也", "还", "都", "很", "但", "却",
    "倒", "仿佛", "似乎", "好像", "一时", "总觉得", "倒也", "不知",
    "竟", "已经", "只是", "而", "又", "才", "再",
]

# 与 RQ3 相同的高频叙事动词表
VERBS = [
    "看", "说", "问", "走", "等", "听", "推", "接", "点", "摇",
    "捧", "收", "应", "站", "坐", "翻", "擦", "敲", "记",
]

# RQ5 新增：常见的中文AI小说“套话/过渡短语”粗糙清单（凭经验列出，未经任何统计验证，
# 仅作为一种极简单、极表层的“AI-ness”代理信号——密度越高不代表“一定是AI”，只是本
# pilot自行设计的一个观察维度，用于和统计距离代理交叉参照）。
AI_CLICHE_PHRASES = [
    "仿佛", "似乎", "不禁", "缓缓", "不由得", "悄然", "静静地", "轻轻地",
    "缓缓地", "微微", "隐隐", "渐渐", "不知不觉", "若有所思", "心中一动",
    "若隐若现", "一时之间", "心头", "眼神复杂",
]


def load_text(rel_paths):
    parts = []
    for rel in rel_paths:
        p = BASE / rel
        parts.append(p.read_text(encoding="utf-8"))
    return "\n".join(parts)


def strip_to_chars(text):
    """仅保留汉字字符（用于字符级TTR、bigram等），去掉标点/空白/引号等。"""
    return re.findall(r"[一-鿿]", text)


def split_sentences(text):
    """按句末标点（。！？…）切分句子，用于平均句长统计。"""
    raw = re.split(r"[。！？…]+", text)
    sentences = [s for s in (seg.strip() for seg in raw) if s]
    return sentences


def char_ngrams(chars, n=2):
    return ["".join(chars[i:i + n]) for i in range(len(chars) - n + 1)]


def compute_features(text):
    chars = strip_to_chars(text)
    n_chars = len(chars)
    if n_chars == 0:
        raise ValueError("文本不含汉字字符，无法计算特征")

    char_ttr = len(set(chars)) / n_chars

    bigrams = char_ngrams(chars, 2)
    bigram_ttr = len(set(bigrams)) / len(bigrams) if bigrams else 0.0

    sentences = split_sentences(text)
    sent_lens = [len(strip_to_chars(s)) for s in sentences]
    avg_sentence_len = sum(sent_lens) / len(sent_lens) if sent_lens else 0.0

    comma_count = len(re.findall(r"[，、；：]", text))
    period_count = len(re.findall(r"[。！？]", text))
    dash_count = len(re.findall(r"——", text))
    quote_count = len(re.findall(r"[\"“”]", text))
    ellipsis_count = len(re.findall(r"\.\.\.|……", text))

    def density(count):
        return count / n_chars * 100.0

    comma_density = density(comma_count)
    period_density = density(period_count)
    dash_density = density(dash_count)
    quote_density = density(quote_count)
    ellipsis_density = density(ellipsis_count)

    fw_counts = {w: text.count(w) for w in FUNCTION_WORDS}
    fw_density = {w: c / n_chars * 100.0 for w, c in fw_counts.items()}

    verb_counts = {v: text.count(v) for v in VERBS}
    verb_density = {v: c / n_chars * 100.0 for v, c in verb_counts.items()}

    # RQ5 新增：AI套话短语密度（每100字）
    cliche_counts = {p: text.count(p) for p in AI_CLICHE_PHRASES}
    cliche_density = {p: c / n_chars * 100.0 for p, c in cliche_counts.items()}
    total_cliche_density = sum(cliche_counts.values()) / n_chars * 100.0

    return {
        "n_chars": n_chars,
        "n_sentences": len(sentences),
        "char_ttr": char_ttr,
        "bigram_ttr": bigram_ttr,
        "avg_sentence_len": avg_sentence_len,
        "comma_density": comma_density,
        "period_density": period_density,
        "dash_density": dash_density,
        "quote_density": quote_density,
        "ellipsis_density": ellipsis_density,
        "fw_density": fw_density,
        "verb_density": verb_density,
        "cliche_density": cliche_density,
        "total_cliche_density": total_cliche_density,
    }


def flatten_vector(feat):
    """把 compute_features 的结果展平成定长数值向量，用于距离计算。
    （与RQ3保持一致，不把cliche密度纳入统计距离特征，cliche密度作为独立的第二信号单列报告，
    避免把“手工挑的AI提示词”直接混进“风格统计特征”导致两个代理信号互相污染。）
    """
    vec = [
        feat["char_ttr"],
        feat["bigram_ttr"],
        feat["avg_sentence_len"],
        feat["comma_density"],
        feat["period_density"],
        feat["dash_density"],
        feat["quote_density"],
        feat["ellipsis_density"],
    ]
    vec += [feat["fw_density"][w] for w in FUNCTION_WORDS]
    vec += [feat["verb_density"][v] for v in VERBS]
    return vec


def zscore_matrix(vectors):
    n_dims = len(vectors[0])
    n_docs = len(vectors)
    means = [sum(v[d] for v in vectors) / n_docs for d in range(n_dims)]
    stds = []
    for d in range(n_dims):
        var = sum((v[d] - means[d]) ** 2 for v in vectors) / n_docs
        stds.append(math.sqrt(var) if var > 1e-12 else 1.0)
    z = []
    for v in vectors:
        z.append([(v[d] - means[d]) / stds[d] for d in range(n_dims)])
    return z


def euclidean(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def cosine_sim(a, b):
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na < 1e-12 or nb < 1e-12:
        return 0.0
    return dot / (na * nb)


def main():
    raw_features = {}
    raw_vectors = {}
    for name, paths in CONDITIONS.items():
        text = load_text(paths)
        feat = compute_features(text)
        raw_features[name] = feat
        raw_vectors[name] = flatten_vector(feat)

    names = list(CONDITIONS.keys())
    vectors_list = [raw_vectors[n] for n in names]
    z_vectors_list = zscore_matrix(vectors_list)
    z_vectors = {n: z_vectors_list[i] for i, n in enumerate(names)}

    print("=" * 70)
    print("原始特征摘要（每条件）")
    print("=" * 70)
    for n in names:
        f = raw_features[n]
        print(f"\n[{n}]  n_chars={f['n_chars']}  n_sentences={f['n_sentences']}")
        print(f"  char_ttr={f['char_ttr']:.4f}  bigram_ttr={f['bigram_ttr']:.4f}  "
              f"avg_sentence_len={f['avg_sentence_len']:.2f}")
        print(f"  comma_density={f['comma_density']:.2f}  period_density={f['period_density']:.2f}  "
              f"dash_density={f['dash_density']:.2f}  quote_density={f['quote_density']:.2f}  "
              f"ellipsis_density={f['ellipsis_density']:.2f}")
        print(f"  total_cliche_density(每100字)={f['total_cliche_density']:.3f}")
        top_cliche = sorted(f["cliche_density"].items(), key=lambda x: -x[1])[:6]
        print("  高频AI套话(每100字): " + ", ".join(f"{w}:{c:.3f}" for w, c in top_cliche if c > 0) or "  高频AI套话: 无")

    print("\n" + "=" * 70)
    print("欧氏距离矩阵（基于z-score标准化后的统计特征向量，不含cliche密度）")
    print("=" * 70)
    header = "\t".join([""] + names)
    print(header)
    dist_matrix = {}
    for n1 in names:
        row = [n1]
        dist_matrix[n1] = {}
        for n2 in names:
            d = euclidean(z_vectors[n1], z_vectors[n2])
            dist_matrix[n1][n2] = d
            row.append(f"{d:.3f}")
        print("\t".join(row))

    print("\n" + "=" * 70)
    print("余弦相似度矩阵（基于原始密度向量，未z-score）")
    print("=" * 70)
    cos_matrix = {}
    print(header)
    for n1 in names:
        row = [n1]
        cos_matrix[n1] = {}
        for n2 in names:
            c = cosine_sim(raw_vectors[n1], raw_vectors[n2])
            cos_matrix[n1][n2] = c
            row.append(f"{c:.4f}")
        print("\t".join(row))

    print("\n" + "=" * 70)
    print("核心方向性对比：ai_draft / ai_revised 与 human_simulated 的统计距离")
    print("=" * 70)
    d_draft_human = dist_matrix["ai_draft"]["human_simulated"]
    d_revised_human = dist_matrix["ai_revised"]["human_simulated"]
    print(f"   ai_draft   <-> human_simulated: {d_draft_human:.4f}")
    print(f"   ai_revised <-> human_simulated: {d_revised_human:.4f}")
    if d_revised_human < d_draft_human:
        direction = "ai_revised 比 ai_draft 更接近 human_simulated（修订后统计距离上更像“人类模拟文本”）"
    elif d_revised_human > d_draft_human:
        direction = "ai_revised 比 ai_draft 更远离 human_simulated（修订后统计距离上反而更不像“人类模拟文本”）"
    else:
        direction = "ai_draft 与 ai_revised 到 human_simulated 的距离相等（本pilot精度下无法区分方向）"
    print(f"   -> 方向性观察: {direction}")

    print("\n核心方向性对比二：AI套话总密度（每100字）")
    cliche_human = raw_features["human_simulated"]["total_cliche_density"]
    cliche_draft = raw_features["ai_draft"]["total_cliche_density"]
    cliche_revised = raw_features["ai_revised"]["total_cliche_density"]
    print(f"   human_simulated: {cliche_human:.4f}")
    print(f"   ai_draft:        {cliche_draft:.4f}")
    print(f"   ai_revised:      {cliche_revised:.4f}")

    output = {
        "_disclaimer": (
            "以下全部数字均为手工统计特征距离/密度代理，不是embedding可分性检验，"
            "不是StoryScope检测器，不是训练过的分类器。human_simulated条件本身是AI（本agent）"
            "模拟人类写作产出的替代文本，不是真实人类语料，因此本文件中任何“更像人类”"
            "的表述都仅指“更接近本次AI模拟的人类替代文本”，与真实人类写作的接近程度未知。"
        ),
        "raw_features": raw_features,
        "euclidean_distance_matrix": dist_matrix,
        "cosine_similarity_matrix": cos_matrix,
        "direction_ai_draft_vs_ai_revised_distance_to_human_simulated": {
            "ai_draft_to_human_simulated": d_draft_human,
            "ai_revised_to_human_simulated": d_revised_human,
            "observation": direction,
        },
        "cliche_density_total_per_100chars": {
            "human_simulated": cliche_human,
            "ai_draft": cliche_draft,
            "ai_revised": cliche_revised,
        },
    }
    out_path = Path(__file__).resolve().parent / "stylometric_results_rq5.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {out_path}")


if __name__ == "__main__":
    main()
