"""차트 Agent: 이평선, RSI, MACD, 볼린저밴드로 매매 타이밍을 판단."""

from utils.llm import call_llm_json
from utils.prompts import chart_prompt, revise_prompt

AGENT_KEY = "chart"
AGENT_LABEL = "차트"

SCHEMA = (
    '{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "차트 지표별 분석 3~5줄"}'
)

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "reason": "데이터 부족으로 판단 보류",
    "detail": "기술적 지표를 충분히 확보하지 못해 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = chart_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}


def revise(state: dict) -> dict:
    opinions = state.get("opinions", {})
    own_opinion = opinions.get(AGENT_KEY, FALLBACK)
    peer_opinions = {k: v for k, v in opinions.items() if k != AGENT_KEY}
    system_prompt, user_prompt = revise_prompt(AGENT_LABEL, own_opinion, peer_opinions, SCHEMA)
    result = call_llm_json(system_prompt, user_prompt, own_opinion)
    return {"opinions": {AGENT_KEY: result}}
