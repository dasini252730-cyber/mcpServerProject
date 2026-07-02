"""매크로 Agent: 금리, 달러, 경기 사이클이 종목에 유리한지 판단."""

from utils.llm import call_llm_json
from utils.prompts import macro_prompt, revise_prompt

AGENT_KEY = "macro"
AGENT_LABEL = "매크로"

SCHEMA = (
    '{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "매크로 환경 분석 3~5줄"}'
)

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "reason": "데이터 부족으로 판단 보류",
    "detail": "매크로 지표를 충분히 확보하지 못해 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = macro_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}


def revise(state: dict) -> dict:
    opinions = state.get("opinions", {})
    own_opinion = opinions.get(AGENT_KEY, FALLBACK)
    peer_opinions = {k: v for k, v in opinions.items() if k != AGENT_KEY}
    system_prompt, user_prompt = revise_prompt(AGENT_LABEL, own_opinion, peer_opinions, SCHEMA)
    result = call_llm_json(system_prompt, user_prompt, own_opinion)
    return {"opinions": {AGENT_KEY: result}}
