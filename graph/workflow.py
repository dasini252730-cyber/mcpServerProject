"""LangGraph 흐름 설계: 데이터수집 -> 6개 병렬분석 -> Orchestrator 종합 -> 리포트 생성."""

from langgraph.graph import END, StateGraph

from agents import (
    behavioral_agent,
    chart_agent,
    macro_agent,
    orchestrator,
    quant_agent,
    risk_agent,
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


def build_graph():
    graph = StateGraph(StockState)

    # Node 등록
    graph.add_node("collect_data", collect_data_node)
    graph.add_node("analyze_value", value_agent.analyze)
    graph.add_node("analyze_quant", quant_agent.analyze)
    graph.add_node("analyze_macro", macro_agent.analyze)
    graph.add_node("analyze_chart", chart_agent.analyze)
    graph.add_node("analyze_risk", risk_agent.analyze)
    graph.add_node("analyze_behavioral", behavioral_agent.analyze)
    graph.add_node("orchestrate", orchestrator.synthesize)
    graph.add_node("generate_report", generate_report_node)

    # Edge 연결
    graph.set_entry_point("collect_data")

    # 데이터 수집 후 6개 Agent 병렬 실행
    graph.add_edge("collect_data", "analyze_value")
    graph.add_edge("collect_data", "analyze_quant")
    graph.add_edge("collect_data", "analyze_macro")
    graph.add_edge("collect_data", "analyze_chart")
    graph.add_edge("collect_data", "analyze_risk")
    graph.add_edge("collect_data", "analyze_behavioral")

    # 6개 완료 후 Orchestrator로 수렴
    graph.add_edge("analyze_value", "orchestrate")
    graph.add_edge("analyze_quant", "orchestrate")
    graph.add_edge("analyze_macro", "orchestrate")
    graph.add_edge("analyze_chart", "orchestrate")
    graph.add_edge("analyze_risk", "orchestrate")
    graph.add_edge("analyze_behavioral", "orchestrate")

    # 최종 리포트 생성
    graph.add_edge("orchestrate", "generate_report")
    graph.add_edge("generate_report", END)

    return graph.compile()
