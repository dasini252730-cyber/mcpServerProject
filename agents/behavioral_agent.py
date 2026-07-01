"""행동경제학 Agent: 뉴스 감성, Fear & Greed Index로 시장 심리와 역발상 신호를 분석."""

from utils.llm import call_llm_json
from utils.prompts import behavioral_prompt

AGENT_KEY = "behavioral"

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
