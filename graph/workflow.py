"""LangGraph 흐름 설계: 데이터수집 -> 6개 병렬분석 -> Orchestrator 종합 -> 리포트 생성."""

from langgraph.graph import END, StateGraph

from agents import (
    behavioral_agent,
    chart_agent,
    macro_agent,
    orchestrator,
    quant_agent,
    risk_agent,
    validator_agent,
    value_agent,
)
from graph.state import StockState
from tools.chart_data import ChartDataTool
from tools.macro_data import MacroDataTool
from tools.market_data import MarketDataTool
from tools.news_data import NewsDataTool
from utils.formatter import format_report


def collect_data_node(state: dict) -> dict:
    import yfinance as yf

    from tools.yf_session import get_session

    ticker = state["ticker"]
    company_name = state.get("company_name")
    if not company_name:
        try:
            company_name = yf.Ticker(ticker, session=get_session()).info.get("shortName") or ticker
        except Exception:  # noqa: BLE001
            company_name = ticker

    errors = []

    try:
        market_data = MarketDataTool.get_all(ticker)
    except Exception as exc:  # noqa: BLE001
        market_data = {}
        errors.append(f"market_data: {exc}")

    try:
        chart_data = ChartDataTool.get_all(ticker)
    except Exception as exc:  # noqa: BLE001
        chart_data = {}
        errors.append(f"chart_data: {exc}")

    try:
        macro_data = MacroDataTool.get_all()
    except Exception as exc:  # noqa: BLE001
        macro_data = {}
        errors.append(f"macro_data: {exc}")

    try:
        news_data = NewsDataTool.get_all(ticker, company_name)
    except Exception as exc:  # noqa: BLE001
        news_data = {}
        errors.append(f"news_data: {exc}")

    return {
        "company_name": company_name,
        "market_data": market_data,
        "chart_data": chart_data,
        "macro_data": macro_data,
        "news_data": news_data,
        "status": "데이터 수집 완료",
        "error": "; ".join(errors) if errors else None,
    }


def generate_report_node(state: dict) -> dict:
    return {
        "report": format_report(state),
        "status": "완료",
    }


AGENT_MODULES = {
    "value": value_agent,
    "quant": quant_agent,
    "macro": macro_agent,
    "chart": chart_agent,
    "risk": risk_agent,
    "behavioral": behavioral_agent,
}


def build_graph():
    graph = StateGraph(StockState)

    # Node 등록
    graph.add_node("collect_data", collect_data_node)
    for key, module in AGENT_MODULES.items():
        graph.add_node(f"analyze_{key}", module.analyze)
        graph.add_node(f"revise_{key}", module.revise)
    graph.add_node("validate", validator_agent.validate)
    graph.add_node("orchestrate", orchestrator.synthesize)
    graph.add_node("generate_report", generate_report_node)

    # Edge 연결
    graph.set_entry_point("collect_data")

    # 1차 라운드: 데이터 수집 후 6개 Agent 독립 병렬 분석
    for key in AGENT_MODULES:
        graph.add_edge("collect_data", f"analyze_{key}")

    # 2차 라운드: 6개 1차 분석이 모두 끝난 뒤에만 각 Agent의 재검토가 시작되도록
    # barrier를 건다 (각 revise 노드는 자신을 포함한 6개 analyze 노드 전부에 의존).
    # 재검토 단계에서 각 Agent는 자신의 1차 의견과 동료 5명의 1차 의견을 함께 보고
    # 판단을 유지하거나 조정한다.
    for revise_key in AGENT_MODULES:
        for analyze_key in AGENT_MODULES:
            graph.add_edge(f"analyze_{analyze_key}", f"revise_{revise_key}")

    # 재검토된 6개 의견이 모두 끝난 후 검증 단계로 수렴: 각 Agent의 판단이 실제
    # 근거 데이터에 기반하는지 확인한다 (데이터가 없는데 확신에 찬 판단을 내놓는 것 방지).
    for key in AGENT_MODULES:
        graph.add_edge(f"revise_{key}", "validate")

    # 검증 결과를 반영해 Orchestrator가 최종 종합
    graph.add_edge("validate", "orchestrate")

    # 최종 리포트 생성
    graph.add_edge("orchestrate", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()
