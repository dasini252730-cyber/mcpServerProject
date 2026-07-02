"""StockMind FastAPI 백엔드: 정적 프론트엔드 서빙 + SSE 분석 API.

Streamlit 대신 사용하는 경량 대체제. 같은 프로세스가 화면(static/)과
분석 API를 함께 서빙하므로 배포 대상이 하나로 끝난다.
"""

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from graph.state import merge_dicts, merge_errors
from graph.workflow import build_graph
from utils.formatter import agent_evidence, format_report, opinions_table_rows

load_dotenv()

BASE_DIR = Path(__file__).parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="StockMind")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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
    "validate": "근거 데이터 검증",
    "orchestrate": "Orchestrator 종합",
    "generate_report": "리포트 생성",
}

_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def _merge_update(final_state: dict, update: dict) -> None:
    for key, value in update.items():
        if key == "opinions":
            final_state["opinions"] = merge_dicts(final_state.get("opinions"), value)
        elif key == "error":
            final_state["error"] = merge_errors(final_state.get("error"), value)
        else:
            final_state[key] = value


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


def _build_initial_state(ticker: str, company_name: str, question: str) -> dict:
    return {
        "ticker": ticker.strip().upper(),
        "question": question.strip() or "지금 매수해도 될까?",
        "company_name": company_name.strip(),
        "market_data": {},
        "macro_data": {},
        "news_data": {},
        "chart_data": {},
        "opinions": {},
        "validation": {},
        "final_verdict": "",
        "final_score": 0.0,
        "confidence": "",
        "final_reason": "",
        "dissenting_opinion": "",
        "excluded_agents": [],
        "report": "",
        "error": None,
        "status": "시작",
    }


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/pipeline")
def pipeline():
    return NODE_LABELS


@app.get("/api/analyze/stream")
async def analyze_stream(
    ticker: str = Query(...),
    company_name: str = Query(""),
    question: str = Query("지금 매수해도 될까?"),
):
    if not ticker.strip():
        return StreamingResponse(
            iter([_sse("error", {"message": "종목 코드를 입력해주세요."})]),
            media_type="text/event-stream",
        )

    graph = get_graph()
    initial_state = _build_initial_state(ticker, company_name, question)

    async def event_generator():
        final_state = dict(initial_state)
        loop = asyncio.get_event_loop()
        queue: asyncio.Queue = asyncio.Queue()

        def run_graph():
            try:
                for chunk in graph.stream(initial_state, stream_mode="updates"):
                    loop.call_soon_threadsafe(queue.put_nowait, ("chunk", chunk))
            except Exception as exc:  # noqa: BLE001
                loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))
            finally:
                loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

        loop.run_in_executor(None, run_graph)

        while True:
            kind, payload = await queue.get()
            if kind == "chunk":
                for node_name, update in payload.items():
                    _merge_update(final_state, update)
                    yield _sse(
                        "progress",
                        {"node": node_name, "label": NODE_LABELS.get(node_name, node_name)},
                    )
            elif kind == "error":
                yield _sse("error", {"message": payload})
                return
            elif kind == "done":
                yield _sse(
                    "result",
                    {
                        "ticker": final_state.get("ticker"),
                        "company_name": final_state.get("company_name"),
                        "final_verdict": final_state.get("final_verdict"),
                        "final_score": final_state.get("final_score"),
                        "confidence": final_state.get("confidence"),
                        "final_reason": final_state.get("final_reason"),
                        "dissenting_opinion": final_state.get("dissenting_opinion"),
                        "opinions": final_state.get("opinions"),
                        "opinions_table": opinions_table_rows(
                            final_state.get("opinions", {}), final_state.get("validation", {})
                        ),
                        "evidence": agent_evidence(final_state),
                        "validation": final_state.get("validation"),
                        "excluded_agents": final_state.get("excluded_agents"),
                        "data_error": final_state.get("error"),
                        "report": final_state.get("report") or format_report(final_state),
                    },
                )
                return

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
