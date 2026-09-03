# -*- coding: utf-8 -*-
"""
RQ4 pilot 成本估算脚本。

重要说明：
- 本脚本的所有"token数"均为估算代理值，不是真实API返回的usage字段（因为本pilot是人工模拟
  三种生成策略而非真实多模型调用），估算方法：中文字符数 * TOKENS_PER_CHAR 系数。
- 定价数量级参照2025-2026年公开定价（强模型如Claude Sonnet/GPT-4.1量级 input $3/output $15
  每百万token；廉价模型如DeepSeek-V4-Flash/Qwen量级 input $0.15/output $0.6 每百万token；
  judge/checker模型采用与drafter/reviser池不重叠的中间档，input $0.5/output $2 每百万token），
  非实时价格，仅用于估算成本量级与三种策略间的相对差异。
- Pipeline 顺序（复用文档2.2节）：Drafter生成草稿 -> Consistency Checker + Narratology
  Checker检查草稿 -> Reviser结合issue生成final_text。三种策略统一走1轮修正，checker模型
  在三种策略间保持一致（同一judge模型），以保证成本对比的公平性——变化的是被检查文本本身
  的长度和质量（草稿质量越差，checker输出的issue列表通常越长）。
"""
import json
import os

# ---------- 全局假设 ----------
TOKENS_PER_CHAR = 1.8  # 中文字符 -> token 的估算系数（近似值，非精确分词结果）

PRICE = {
    # 单位：美元 / 1M tokens
    "strong": {"input": 3.00, "output": 15.00},   # 对标 Claude Sonnet 4.6 / GPT-4.1 量级
    "cheap":  {"input": 0.15, "output": 0.60},    # 对标 DeepSeek-V4-Flash / Qwen3-14B 量级
    "judge":  {"input": 0.50, "output": 2.00},    # 与drafter/reviser池不重叠的中间档 judge/checker
}

CONTEXT_CHARS = 3139          # master_ground_truth.json 有效字符数（世界观+角色卡+契科夫的枪）
DRAFTER_PROMPT_OVERHEAD = 600  # drafter 系统提示+章节大纲指令等模板开销（字符数代理）
REVISE_CONTEXT_SUBSET = 1600   # reviser 需要的角色红线/世界观子集（非全量）
REVISE_PROMPT_OVERHEAD = 500
CHECKER_CONTEXT_SUBSET = 1600  # checker 需要核对红线的角色/世界观子集
CHECKER_PROMPT_OVERHEAD = 900  # 一致性/叙事规则checklist模板开销（pilot用简化版rubric代理304类narratology体系）

# 观测到的实际文本字符数（不含换行，来自 eval/_count_chars.py 输出）
OBS = {
    "A": {"ch1_final": 1319, "ch2_final": 1149},
    "B": {"ch1_final": 521, "ch2_final": 362},
    "C": {
        "ch1_draft": 378, "ch1_final": 1070,
        "ch2_draft": 362, "ch2_final": 788,
    },
}

# A、B 只保留了 revise 后的最终文本，未单独保存草稿快照；
# 按典型质量差距估算草稿相对最终文本的字符比例（用于成本建模，非精确还原）：
#   A（强drafter）：草稿已接近成稿，revise只是轻度打磨，草稿约为最终的88%
#   B（廉价drafter+廉价reviser）：revise提升有限，草稿约为最终的82%
DRAFT_RATIO = {"A": 0.88, "B": 0.82}

# checker 在检查"较弱草稿"时通常输出更长的issue列表（发现更多问题需要更多文字描述）
# 对应本方案要求的"checker成本必须纳入核算"——弱草稿会拉高checker环节的output token
CHECKER_OUTPUT_CHARS_PER_CALL = {
    "A": 150,   # 强模型草稿本身问题少，issue列表简短
    "B": 280,   # 廉价草稿问题较多（骨架化、伏笔处理生硬、红线擦边），issue列表更长
    "C": 280,   # C的草稿由同一个cheap drafter生成，checker检查对象与B同质，issue列表长度相当
}


def tokens(chars):
    return chars * TOKENS_PER_CHAR


def call_cost(input_chars, output_chars, tier):
    in_tok = tokens(input_chars)
    out_tok = tokens(output_chars)
    cost = in_tok / 1_000_000 * PRICE[tier]["input"] + out_tok / 1_000_000 * PRICE[tier]["output"]
    return {
        "input_chars": input_chars,
        "output_chars": output_chars,
        "input_tokens_est": round(in_tok, 1),
        "output_tokens_est": round(out_tok, 1),
        "tier": tier,
        "cost_usd": round(cost, 6),
    }


def build_strategy_A():
    chapters = {}
    for ch in ["ch1", "ch2"]:
        final_chars = OBS["A"][f"{ch}_final"]
        draft_chars = round(final_chars * DRAFT_RATIO["A"])

        drafter = call_cost(CONTEXT_CHARS + DRAFTER_PROMPT_OVERHEAD, draft_chars, "strong")

        checker_out = CHECKER_OUTPUT_CHARS_PER_CALL["A"]
        consistency_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")
        narratology_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")

        issues_chars = consistency_checker["output_chars"] + narratology_checker["output_chars"]
        reviser = call_cost(draft_chars + issues_chars + REVISE_CONTEXT_SUBSET + REVISE_PROMPT_OVERHEAD, final_chars, "strong")

        chapters[ch] = {
            "drafter_call": drafter,
            "consistency_checker_call": consistency_checker,
            "narratology_checker_call": narratology_checker,
            "reviser_call": reviser,
        }
    return chapters


def build_strategy_B():
    chapters = {}
    for ch in ["ch1", "ch2"]:
        final_chars = OBS["B"][f"{ch}_final"]
        draft_chars = round(final_chars * DRAFT_RATIO["B"])

        drafter = call_cost(CONTEXT_CHARS + DRAFTER_PROMPT_OVERHEAD, draft_chars, "cheap")

        checker_out = CHECKER_OUTPUT_CHARS_PER_CALL["B"]
        consistency_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")
        narratology_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")

        issues_chars = consistency_checker["output_chars"] + narratology_checker["output_chars"]
        # 全廉价策略：reviser 也用 cheap 模型
        reviser = call_cost(draft_chars + issues_chars + REVISE_CONTEXT_SUBSET + REVISE_PROMPT_OVERHEAD, final_chars, "cheap")

        chapters[ch] = {
            "drafter_call": drafter,
            "consistency_checker_call": consistency_checker,
            "narratology_checker_call": narratology_checker,
            "reviser_call": reviser,
        }
    return chapters


def build_strategy_C():
    chapters = {}
    for ch in ["ch1", "ch2"]:
        draft_chars = OBS["C"][f"{ch}_draft"]
        final_chars = OBS["C"][f"{ch}_final"]

        # cheap drafter（与B同源模型）
        drafter = call_cost(CONTEXT_CHARS + DRAFTER_PROMPT_OVERHEAD, draft_chars, "cheap")

        checker_out = CHECKER_OUTPUT_CHARS_PER_CALL["C"]
        consistency_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")
        narratology_checker = call_cost(draft_chars + CHECKER_CONTEXT_SUBSET + CHECKER_PROMPT_OVERHEAD, checker_out, "judge")

        issues_chars = consistency_checker["output_chars"] + narratology_checker["output_chars"]
        # 路由核心：reviser 用 strong 模型
        reviser = call_cost(draft_chars + issues_chars + REVISE_CONTEXT_SUBSET + REVISE_PROMPT_OVERHEAD, final_chars, "strong")

        chapters[ch] = {
            "drafter_call": drafter,
            "consistency_checker_call": consistency_checker,
            "narratology_checker_call": narratology_checker,
            "reviser_call": reviser,
        }
    return chapters


def summarize(chapters):
    total = 0.0
    checker_total = 0.0
    drafter_total = 0.0
    reviser_total = 0.0
    for ch, calls in chapters.items():
        for name, c in calls.items():
            total += c["cost_usd"]
            if "checker" in name:
                checker_total += c["cost_usd"]
            elif name == "drafter_call":
                drafter_total += c["cost_usd"]
            elif name == "reviser_call":
                reviser_total += c["cost_usd"]
    return {
        "total_cost_usd": round(total, 6),
        "drafter_cost_usd": round(drafter_total, 6),
        "reviser_cost_usd": round(reviser_total, 6),
        "checker_cost_usd": round(checker_total, 6),
        "checker_pct_of_total": round(checker_total / total * 100, 2) if total else 0,
    }


def main():
    strategies = {
        "strategy_A_allstrong": build_strategy_A(),
        "strategy_B_allcheap": build_strategy_B(),
        "strategy_C_router": build_strategy_C(),
    }

    out = {
        "assumptions": {
            "note": "以下为按公开定价量级估算的模拟成本，非真实API usage字段返回值；本pilot为人工模拟三种策略，未发生真实多模型API调用。",
            "tokens_per_char": TOKENS_PER_CHAR,
            "pricing_usd_per_1M_tokens": PRICE,
            "context_chars_ground_truth": CONTEXT_CHARS,
            "drafter_prompt_overhead_chars": DRAFTER_PROMPT_OVERHEAD,
            "revise_context_subset_chars": REVISE_CONTEXT_SUBSET,
            "revise_prompt_overhead_chars": REVISE_PROMPT_OVERHEAD,
            "checker_context_subset_chars": CHECKER_CONTEXT_SUBSET,
            "checker_prompt_overhead_chars": CHECKER_PROMPT_OVERHEAD,
            "draft_ratio_assumption": DRAFT_RATIO,
            "checker_output_chars_per_call": CHECKER_OUTPUT_CHARS_PER_CALL,
            "pipeline_order": "Drafter生成草稿 -> Consistency Checker + Narratology Checker检查草稿 -> Reviser结合issue生成final_text（复用研究方案2.2节pipeline）",
        },
        "strategies": {},
    }

    for name, chapters in strategies.items():
        out["strategies"][name] = {
            "chapters": chapters,
            "summary": summarize(chapters),
        }

    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "cost_estimates.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print("=== 成本汇总 ===")
    for name in strategies:
        s = out["strategies"][name]["summary"]
        print(name, s)


if __name__ == "__main__":
    main()
