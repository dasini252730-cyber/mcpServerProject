"""Orchestrator Agent: 6개 Agent 의견을 가중치 기반으로 종합해 최종 판단을 내린다.

점수/판단/신뢰도는 결정적(deterministic) 산술로 계산하고, LLM은 그 결과에
이르게 된 핵심 근거와 소수 의견을 서술하는 데에만 사용한다. (LLM에게 산술
자체를 맡기면 재현성이 떨어지고 검증이 어렵기 때문)
"""

from utils.llm import call_llm_json
from utils.prompts import orchestrator_prompt

WEIGHTS = {
    "value": 1.2,
    "quant": 1.3,
    "macro": 1.0,
    "chart": 0.8,
    "risk": 1.5,
    "behavioral": 0.9,
}

NARRATIVE_FALLBACK = {
    "key_reason": "각 Agent 의견을 가중 평균한 결과를 바탕으로 판단했습니다.",
    "dissenting_opinion": "",
}


def _score_to_verdict(score: float) -> str:
    if score >= 65:
        return "매수"
    if score >= 40:
        return "관망"
    return "매도"


def synthesize(state: dict) -> dict:
    opinions = state.get("opinions", {})

    weighted_sum = 0.0
    weight_total = 0.0
    verdict_counts = {"매수": 0, "관망": 0, "매도": 0}

    for key, weight in WEIGHTS.items():
        op = opinions.get(key)
        if not op:
            continue
        score = op.get("score", 50) or 50
        weighted_sum += score * weight
        weight_total += weight
        verdict = op.get("verdict", "관망")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1

    final_score = weighted_sum / weight_total if weight_total else 50.0
    final_verdict = _score_to_verdict(final_score)

    total_votes = sum(verdict_counts.values()) or 1
    agreement_ratio = max(verdict_counts.values()) / total_votes
    if agreement_ratio >= 0.8:
        confidence = "높음"
    elif agreement_ratio >= 0.5:
        confidence = "보통"
    else:
        confidence = "낮음"

    dissenters = [
        f"{key}: {op.get('verdict')} ({op.get('reason', '')})"
        for key, op in opinions.items()
        if op.get("verdict") != final_verdict
    ]
    default_dissenting = "; ".join(dissenters)

    system_prompt, user_prompt = orchestrator_prompt(state, final_verdict, final_score, confidence)
    narrative = call_llm_json(system_prompt, user_prompt, NARRATIVE_FALLBACK)

    return {
        "final_verdict": final_verdict,
        "final_score": final_score,
        "confidence": confidence,
        "final_reason": narrative.get("key_reason", NARRATIVE_FALLBACK["key_reason"]),
        "dissenting_opinion": narrative.get("dissenting_opinion") or default_dissenting,
    }
