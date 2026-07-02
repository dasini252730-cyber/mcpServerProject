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


def opinions_table_rows(opinions: dict, validation: dict = None) -> list[dict]:
    validation = validation or {}
    rows = []
    for key in AGENT_ORDER:
        op = opinions.get(key)
        if not op:
            continue
        grounded = validation.get(key, {}).get("grounded", True)
        row = {
            "Agent": AGENT_LABELS.get(key, key),
            "판단": f"{verdict_emoji(op.get('verdict', ''))} {op.get('verdict', '-')}",
            "점수": op.get("score", "-"),
            "핵심 근거": op.get("reason", "-"),
            "근거 확인": "✅ 확인됨" if grounded else "⚠️ 근거 부족",
            "오류 (LLM 호출 실패)": op.get("error", ""),
        }
        rows.append(row)
    return rows


def agent_evidence(state: dict) -> dict:
    """각 Agent가 실제로 근거로 삼은 원본 데이터를 뽑아준다.

    utils/prompts.py의 각 *_prompt() 함수가 state에서 어떤 부분을 꺼내
    프롬프트에 넣는지와 동일한 매핑을 사용해, "왜 이런 판단이 나왔는지"를
    화면에서 확인할 수 있게 한다.
    """
    market = state.get("market_data", {})
    macro = state.get("macro_data", {})
    news = state.get("news_data", {})
    return {
        "value": market.get("financial", {}),
        "quant": {**market.get("financial", {}), **market.get("momentum", {})},
        "macro": macro,
        "chart": state.get("chart_data", {}),
        "risk": market.get("volatility", {}),
        "behavioral": {
            "news_sentiment": news.get("sentiment", {}),
            "fear_greed": macro.get("fear_greed", {}),
        },
    }


def _flatten_evidence(data: dict, prefix: str = "") -> list[tuple[str, object]]:
    items = []
    for key, value in data.items():
        label = f"{prefix}{key}"
        if isinstance(value, dict):
            items.extend(_flatten_evidence(value, prefix=f"{label}."))
        elif value not in (None, "", "note"):
            items.append((label, value))
    return items


def format_report(state: dict) -> str:
    ticker = state.get("ticker", "")
    company_name = state.get("company_name", "")
    final_verdict = state.get("final_verdict", "관망")
    final_score = state.get("final_score", 0)
    confidence = state.get("confidence", "-")
    final_reason = state.get("final_reason", "")
    dissenting_opinion = state.get("dissenting_opinion", "")
    opinions = state.get("opinions", {})
    validation = state.get("validation", {})
    evidence = agent_evidence(state)

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

        agent_validation = validation.get(key)
        if agent_validation and not agent_validation.get("grounded", True):
            note = agent_validation.get("note", "")
            lines.append(f"- ⚠️ 근거 검증 실패 — 최종 판단에서 제외됨: {note}")

        evidence_items = _flatten_evidence(evidence.get(key, {}))
        if evidence_items:
            lines.append("")
            lines.append("**근거 데이터**")
            for label, value in evidence_items:
                lines.append(f"- {label}: {value}")
        lines.append("")

    lines += [
        "---",
        "⚠️ 본 분석은 참고용이며 투자 결정은 본인 책임입니다.",
    ]
    return "\n".join(lines)
