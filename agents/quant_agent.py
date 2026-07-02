"""퀀트 Agent: 모멘텀/퀄리티/밸류/사이즈 팩터를 점수화해 종합 평가."""

from utils.llm import call_llm_json
from utils.prompts import quant_prompt, revise_prompt

AGENT_KEY = "quant"
AGENT_LABEL = "퀀트"

SCHEMA = (
    '{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "팩터별 점수 상세"}'
)

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "reason": "데이터 부족으로 판단 보류",
    "detail": "팩터 점수를 계산할 데이터가 충분하지 않아 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = quant_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}


def revise(state: dict) -> dict:
    opinions = state.get("opinions", {})
    own_opinion = opinions.get(AGENT_KEY, FALLBACK)
    peer_opinions = {k: v for k, v in opinions.items() if k != AGENT_KEY}
    system_prompt, user_prompt = revise_prompt(AGENT_LABEL, own_opinion, peer_opinions, SCHEMA)
    result = call_llm_json(system_prompt, user_prompt, own_opinion)
    return {"opinions": {AGENT_KEY: result}}
