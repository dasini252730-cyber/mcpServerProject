"""분석 결과를 Streamlit UI 및 최종 리포트 문자열로 변환하는 헬퍼."""

import datetime

VERDICT_EMOJI = {"매수": "🟢", "관망": "🟡", "매도": "🔴"}

AGENT_LABELS = {
    "value": "가치투자",
    "quant": "퀀트",
    "macro": "매크로",
    "chart": "차트",
    "risk": "리스크",
    "behavioral": "행동경제학",
}

AGENT_ORDER = ["value", "quant", "macro", "chart", "risk", "behavioral"]


def verdict_emoji(verdict: str) -> str:
    return VERDICT_EMOJI.get(verdict, "⚪")


def opinions_table_rows(opinions: dict) -> list[dict]:
    rows = []
    for key in AGENT_ORDER:
        op = opinions.get(key)
        if not op:
            continue
        row = {
            "Agent": AGENT_LABELS.get(key, key),
            "판단": f"{verdict_emoji(op.get('verdict', ''))} {op.get('verdict', '-')}",
            "점수": op.get("score", "-"),
            "핵심 근거": op.get("reason", "-"),
            "오류 (LLM 호출 실패)": op.get("error", ""),
        }
        rows.append(row)
    return rows


def format_report(state: dict) -> str:
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", "")
    final_verdict = state.get("final_verdict", "관망")
    final_score = state.get("final_score", 0)
    confidence = state.get("confidence", "-")
    final_reason = state.get("final_reason", "")
    dissenting_opinion = state.get("dissenting_opinion", "")
    opinions = state.get("opinions", {})

    lines = [
        f"# {company_name} ({ticker}) 분석 리포트",
        f"_생성 시각: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}_",
        "",
        f"## 최종 판단: {verdict_emoji(final_verdict)} {final_verdict}",
        f"- 가중 평균 점수: {final_score:.1f} / 100",
        f"- 신뢰도: {confidence}",
        "",
        "### 핵심 근거",
        final_reason or "-",
    ]

    if dissenting_opinion:
        lines += ["", "### 소수 의견", dissenting_opinion]

    lines += ["", "## Agent별 상세 분석"]
    for key in AGENT_ORDER:
        op = opinions.get(key)
        if not op:
            continue
        lines.append(f"### {AGENT_LABELS.get(key, key)} — {verdict_emoji(op.get('verdict', ''))} {op.get('verdict', '-')} ({op.get('score', '-')}점)")
        lines.append(op.get("detail", op.get("reason", "-")))
        if key == "risk" and op.get("worst_case"):
            lines.append(f"- 최악 시나리오: {op['worst_case']}")
        if key == "behavioral" and op.get("market_emotion"):
            lines.append(f"- 시장 심리: {op['market_emotion']}")
        if op.get("error"):
            lines.append(f"- ⚠️ LLM 호출 실패로 기본값이 사용됨: `{op['error']}`")
        lines.append("")

    lines += [
        "---",
        "⚠️ 본 분석은 참고용이며 투자 결정은 본인 책임입니다.",
    ]
    return "\n".join(lines)
