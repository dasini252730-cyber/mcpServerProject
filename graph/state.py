"""LangGraph State 정의.

6개 분석 Agent가 병렬로 실행되어 'opinions'와 'error' 키에 동시에 쓰기 때문에,
LangGraph의 기본 "덮어쓰기" 동작 대신 병합(reducer) 함수를 지정해야
동시 업데이트 충돌(InvalidUpdateError) 없이 fan-out/fan-in이 가능하다.
"""

from typing import Annotated, Optional, TypedDict


def merge_dicts(left: Optional[dict], right: Optional[dict]) -> dict:
    merged = dict(left or {})
    merged.update(right or {})
    return merged


def merge_errors(left: Optional[str], right: Optional[str]) -> Optional[str]:
    if not left:
        return right
    if not right or left == right:
        return left
    return f"{left} | {right}"


class StockState(TypedDict):
    # 입력
    ticker: str
    question: str
    company_name: str

    # 수집 데이터 (collect_data 노드에서만 기록되므로 병합 불필요)
    market_data: dict
    macro_data: dict
    news_data: dict
    chart_data: dict

    # 6개 Agent가 병렬로 기록 -> 병합 reducer 필요
    opinions: Annotated[dict, merge_dicts]

    # validate 노드가 단독으로 기록: {agent_key: {"grounded": bool, "note": str}}
    validation: dict

    # 최종 결과 (orchestrate/generate_report 노드에서만 기록)
    final_verdict: str
    final_score: float
    confidence: str
    final_reason: str
    dissenting_opinion: str
    excluded_agents: list
    report: str

    # 메타 (여러 노드에서 기록될 수 있어 병합 reducer 필요)
    error: Annotated[Optional[str], merge_errors]
    status: str
