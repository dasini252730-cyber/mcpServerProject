"""StockMind — 멀티에이전트 주식 분석기 (Streamlit UI)."""

import os

import streamlit as st
from dotenv import load_dotenv

from graph.state import merge_dicts, merge_errors
from graph.workflow import build_graph
from utils.formatter import format_report, opinions_table_rows, verdict_emoji

load_dotenv()

st.set_page_config(page_title="StockMind", page_icon="🏦", layout="centered")

NODE_LABELS = {
    "collect_data": "데이터 수집",
    "analyze_value": "가치투자 Agent 1차 분석",
    "analyze_quant": "퀀트 Agent 1차 분석",
    "analyze_macro": "매크로 Agent 1차 분석",
    "analyze_chart": "차트 Agent 1차 분석",
    "analyze_risk": "리스크 Agent 1차 분석",
    "analyze_behavioral": "행동경제학 Agent 1차 분석",
    "revise_value": "가치투자 Agent 동료 의견 반영",
    "revise_quant": "퀀트 Agent 동료 의견 반영",
    "revise_macro": "매크로 Agent 동료 의견 반영",
    "revise_chart": "차트 Agent 동료 의견 반영",
    "revise_risk": "리스크 Agent 동료 의견 반영",
    "revise_behavioral": "행동경제학 Agent 동료 의견 반영",
    "orchestrate": "Orchestrator 종합",
    "generate_report": "리포트 생성",
}
NODE_ORDER = list(NODE_LABELS.keys())


@st.cache_resource
def get_graph():
    return build_graph()


def merge_update(final_state: dict, update: dict) -> None:
    for key, value in update.items():
        if key == "opinions":
            final_state["opinions"] = merge_dicts(final_state.get("opinions"), value)
        elif key == "error":
            final_state["error"] = merge_errors(final_state.get("error"), value)
        else:
            final_state[key] = value


st.title("🏦 StockMind")
st.caption("멀티에이전트 주식 분석기 — 6개의 전문 AI Agent가 종합 판단합니다.")

if not os.getenv("ANTHROPIC_API_KEY"):
    st.warning("ANTHROPIC_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.", icon="⚠️")

with st.form("ticker_form"):
    col1, col2 = st.columns([2, 1])
    with col1:
        ticker = st.text_input(
            "종목 코드",
            placeholder="예: TSLA, AAPL, 005930.KS",
            help="한국 주식은 .KS(코스피)/.KQ(코스닥) 접미사를 붙여주세요.",
        )
    with col2:
        company_name = st.text_input("종목명 (선택)", placeholder="예: Tesla")
    question = st.text_input("질문 (선택)", placeholder="예: 지금 살까?", value="지금 매수해도 될까?")
    submitted = st.form_submit_button("분석 시작", use_container_width=True)

if submitted:
    if not ticker.strip():
        st.error("종목 코드를 입력해주세요.")
        st.stop()

    graph = get_graph()
    initial_state = {
        "ticker": ticker.strip().upper(),
        "question": question.strip() or "지금 매수해도 될까?",
        "company_name": company_name.strip(),
        "market_data": {},
        "macro_data": {},
        "news_data": {},
        "chart_data": {},
        "opinions": {},
        "final_verdict": "",
        "final_score": 0.0,
        "confidence": "",
        "final_reason": "",
        "dissenting_opinion": "",
        "report": "",
        "error": None,
        "status": "시작",
    }

    final_state: dict = dict(initial_state)
    completed_nodes: list[str] = []

    with st.status("분석 진행 중...", expanded=True) as status_box:
        checklist_placeholder = st.empty()
        try:
            for chunk in graph.stream(initial_state, stream_mode="updates"):
                for node_name, update in chunk.items():
                    merge_update(final_state, update)
                    if node_name in NODE_LABELS:
                        completed_nodes.append(node_name)
                    checklist = "\n".join(
                        f"- {'✅' if n in completed_nodes else '⬜'} {label}"
                        for n, label in NODE_LABELS.items()
                    )
                    status_box.update(label=f"진행 중: {NODE_LABELS.get(node_name, node_name)}")
                    checklist_placeholder.markdown(checklist)
            status_box.update(label="분석 완료", state="complete")
        except Exception as exc:  # noqa: BLE001
            status_box.update(label="분석 실패", state="error")
            st.error(f"분석 중 오류가 발생했습니다: {exc}")
            st.stop()

    if final_state.get("error"):
        st.info(f"일부 데이터 수집에 실패했지만 분석을 계속했습니다: {final_state['error']}")

    st.subheader("📊 각 Agent 의견")
    opinions = final_state.get("opinions", {})
    rows = opinions_table_rows(opinions)
    if rows:
        agent_errors = [op["error"] for op in opinions.values() if op.get("error")]
        if agent_errors and len(agent_errors) == len(opinions):
            st.error(
                "모든 Agent의 LLM 호출이 실패해 기본값(관망)만 표시되고 있습니다. "
                "ANTHROPIC_API_KEY가 올바른지, 모델 접근 권한이 있는지 확인하세요.\n\n"
                f"오류 예시: {agent_errors[0]}"
            )
        st.dataframe(rows, hide_index=True, use_container_width=True)
    else:
        st.warning("Agent 의견을 가져오지 못했습니다.")

    st.subheader("🏛️ 최종 판단")
    final_verdict = final_state.get("final_verdict", "-")
    final_score = final_state.get("final_score", 0)
    confidence = final_state.get("confidence", "-")

    st.markdown(f"## {verdict_emoji(final_verdict)} {final_verdict}")
    st.markdown(f"**신뢰도:** {confidence}  |  **가중 평균 점수:** {final_score:.1f} / 100")
    st.write(final_state.get("final_reason", ""))

    if final_state.get("dissenting_opinion"):
        with st.expander("소수 의견 보기"):
            st.write(final_state["dissenting_opinion"])

    with st.expander("전체 리포트 보기"):
        report_text = final_state.get("report") or format_report(final_state)
        st.markdown(report_text)
        st.download_button(
            "리포트 다운로드 (.md)",
            data=report_text,
            file_name=f"{final_state.get('ticker', 'report')}_stockmind_report.md",
            mime="text/markdown",
        )

    st.divider()
    st.caption("⚠️ 본 분석은 참고용이며 투자 결정은 본인 책임입니다.")
