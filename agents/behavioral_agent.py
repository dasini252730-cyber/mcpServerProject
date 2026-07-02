"""행동경제학 Agent: 뉴스 감성, Fear & Greed Index로 시장 심리와 역발상 신호를 분석."""

from utils.llm import call_llm_json
from utils.prompts import behavioral_prompt, revise_prompt

AGENT_KEY = "behavioral"
AGENT_LABEL = "행동경제학"

SCHEMA = (
    '{"verdict": "매수|관망|매도", "score": 0~100 정수, '
    '"market_emotion": "극도의 탐욕|탐욕|중립|공포|극도의 공포", '
    '"contrarian_signal": true 또는 false, "reason": "한 줄 요약", "detail": "심리 지표 분석 3~5줄"}'
)

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "market_emotion": "중립",
    "contrarian_signal": False,
    "reason": "데이터 부족으로 판단 보류",
    "detail": "심리 지표를 충분히 확보하지 못해 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = behavioral_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}


def revise(state: dict) -> dict:
    opinions = state.get("opinions", {})
    own_opinion = opinions.get(AGENT_KEY, FALLBACK)
    peer_opinions = {k: v for k, v in opinions.items() if k != AGENT_KEY}
    system_prompt, user_prompt = revise_prompt(AGENT_LABEL, own_opinion, peer_opinions, SCHEMA)
    result = call_llm_json(system_prompt, user_prompt, own_opinion)
    return {"opinions": {AGENT_KEY: result}}
