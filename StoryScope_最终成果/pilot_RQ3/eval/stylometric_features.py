# -*- coding: utf-8 -*-
"""
RQ3 pilot：纯标准库（re + collections）实现的文本统计特征代理指标。
用于近似模拟“风格指纹可分性”，不调用任何embedding API或外部NLP库。

用法：python stylometric_features.py
输出：每个条件的特征向量、两两欧氏距离矩阵、余弦相似度矩阵、
      以及 self_revised / cross_revised 与三种原始风格的距离对比。
"""
import re
import math
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent

CONDITIONS = {
    "style_X": ["style_X/ch1.txt", "style_X/ch2.txt"],
    "style_Y": ["style_Y/ch1.txt", "style_Y/ch2.txt"],
    "style_Z": ["style_Z/ch1.txt", "style_Z/ch2.txt"],
    "self_revised": ["self_revised/ch1.txt", "self_revised/ch2.txt"],
    "cross_revised": ["cross_revised/ch1.txt", "cross_revised/ch2.txt"],
}

# 固定的虚词/语气词表（现代汉语叙事文本中常见的可统计闭集虚词）
FUNCTION_WORDS = [
    "了", "的", "着", "就", "也", "还", "都", "很", "但", "却",
    "倒", "仿佛", "似乎", "好像", "一时", "总觉得", "倒也", "不知",
    "竟", "已经", "只是", "而", "又", "才", "再"
]

# 与本场景相关、且在三种风格文本中都会出现的高频叙事动词（"看/说/问"等）
VERBS = [
    "看", "说", "问", "走", "等", "听", "推", "接", "点", "摇",
    "捧", "收", "应", "站", "坐", "翻", "擦", "敲", "记"
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

    # 1. 字符级 distinct ratio（type-token ratio）
    char_ttr = len(set(chars)) / n_chars

    # 2. “词级” distinct ratio 的代理：没有分词库，用字符bigram的distinct ratio
    #    近似“词级”多样性（bigram部分对应中文词/词组边界，标准库可实现）
    bigrams = char_ngrams(chars, 2)
    bigram_ttr = len(set(bigrams)) / len(bigrams) if bigrams else 0.0

    # 3. 平均句长（按汉字字符数计）
    sentences = split_sentences(text)
    sent_lens = [len(strip_to_chars(s)) for s in sentences]
    avg_sentence_len = sum(sent_lens) / len(sent_lens) if sent_lens else 0.0

    # 4. 标点密度（每100个汉字字符中的出现次数）
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

    # 5. 虚词/语气词分布（每100字频率）
    fw_counts = {w: text.count(w) for w in FUNCTION_WORDS}
    fw_density = {w: c / n_chars * 100.0 for w, c in fw_counts.items()}

    # 6. 动词使用频率分布（每100字频率）
    verb_counts = {v: text.count(v) for v in VERBS}
    verb_density = {v: c / n_chars * 100.0 for v, c in verb_counts.items()}

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
    }


def flatten_vector(feat):
    """把 compute_features 的结果展平成定长数值向量，用于距离计算。"""
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
    """对每一维做z-score标准化，避免量纲（句长 vs 密度百分比）主导距离。"""
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
        top_fw = sorted(f['fw_density'].items(), key=lambda x: -x[1])[:6]
        print("  高频虚词(每100字): " + ", ".join(f"{w}:{c:.2f}" for w, c in top_fw))
        top_v = sorted(f['verb_density'].items(), key=lambda x: -x[1])[:6]
        print("  高频动词(每100字): " + ", ".join(f"{w}:{c:.2f}" for w, c in top_v))

    print("\n" + "=" * 70)
    print("欧氏距离矩阵（基于z-score标准化后的特征向量）")
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
    print("关键对比：self_revised / cross_revised 与三种原始风格的欧氏距离")
    print("=" * 70)
    for target in ["self_revised", "cross_revised"]:
        print(f"\n[{target}] 与:")
        dists = {orig: dist_matrix[target][orig] for orig in ["style_X", "style_Y", "style_Z"]}
        for orig, d in sorted(dists.items(), key=lambda x: x[1]):
            print(f"   {orig}: {d:.4f}")
        nearest = min(dists, key=dists.get)
        print(f"   -> 最接近: {nearest}")

    print("\n" + "=" * 70)
    print("三种原始风格两两欧氏距离（原始可分性基线）")
    print("=" * 70)
    pairs = [("style_X", "style_Y"), ("style_X", "style_Z"), ("style_Y", "style_Z")]
    for a, b in pairs:
        print(f"   {a} <-> {b}: {dist_matrix[a][b]:.4f}")
    orig_pair_dists = [dist_matrix[a][b] for a, b in pairs]
    avg_orig_pair_dist = sum(orig_pair_dists) / len(orig_pair_dists)
    print(f"   三种原始风格两两距离均值: {avg_orig_pair_dist:.4f}")

    centroid = [sum(z_vectors[n][d] for n in ["style_X", "style_Y", "style_Z"]) / 3
                for d in range(len(z_vectors["style_X"]))]
    dist_to_centroid = {}
    for n in names:
        dist_to_centroid[n] = euclidean(z_vectors[n], centroid)
    print("\n各条件到三风格质心(centroid)的距离：")
    for n in names:
        print(f"   {n}: {dist_to_centroid[n]:.4f}")

    output = {
        "raw_features": raw_features,
        "euclidean_distance_matrix": dist_matrix,
        "cosine_similarity_matrix": cos_matrix,
        "avg_original_pairwise_distance": avg_orig_pair_dist,
        "distance_to_centroid": dist_to_centroid,
    }
    out_path = Path(__file__).resolve().parent / "stylometric_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {out_path}")


if __name__ == "__main__":
    main()
