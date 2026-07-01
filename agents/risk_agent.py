"""리스크 Agent: 베타, MDD, 변동성으로 투자 위험도를 평가."""

from utils.llm import call_llm_json
from utils.prompts import risk_prompt

AGENT_KEY = "risk"

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
