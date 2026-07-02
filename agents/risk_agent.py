"""리스크 Agent: 베타, MDD, 변동성으로 투자 위험도를 평가."""

from utils.llm import call_llm_json
from utils.prompts import revise_prompt, risk_prompt

AGENT_KEY = "risk"
AGENT_LABEL = "리스크"

SCHEMA = (
    '{"verdict": "매수|관망|매도", "score": 0~100 정수(높을수록 저위험), '
    '"risk_level": "고위험|중위험|저위험", "worst_case": "최악 시나리오 한 줄", '
    '"reason": "한 줄 요약", "detail": "리스크 요인 상세"}'
)

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "risk_level": "중위험",
    "worst_case": "데이터 부족으로 최악 시나리오를 산출하지 못했습니다.",
    "reason": "데이터 부족으로 판단 보류",
    "detail": "리스크 지표를 충분히 확보하지 못해 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = risk_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}


def revise(state: dict) -> dict:
    opinions = state.get("opinions", {})
    own_opinion = opinions.get(AGENT_KEY, FALLBACK)
    peer_opinions = {k: v for k, v in opinions.items() if k != AGENT_KEY}
    system_prompt, user_prompt = revise_prompt(AGENT_LABEL, own_opinion, peer_opinions, SCHEMA)
    result = call_llm_json(system_prompt, user_prompt, own_opinion)
    return {"opinions": {AGENT_KEY: result}}
