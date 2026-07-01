"""가치투자 Agent: PER, PBR, ROE 등 재무 지표로 내재가치 대비 주가 적정성을 판단."""

from utils.llm import call_llm_json
from utils.prompts import value_prompt

AGENT_KEY = "value"

FALLBACK = {
    "verdict": "관망",
    "score": 50,
    "reason": "데이터 부족으로 판단 보류",
    "detail": "가치투자 지표를 충분히 확보하지 못해 중립 의견을 제시합니다.",
}


def analyze(state: dict) -> dict:
    system_prompt, user_prompt = value_prompt(state)
    result = call_llm_json(system_prompt, user_prompt, FALLBACK)
    return {"opinions": {AGENT_KEY: result}}
