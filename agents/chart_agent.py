"""차트 Agent: 이평선, RSI, MACD, 볼린저밴드로 매매 타이밍을 판단."""

from utils.llm import call_llm_json
from utils.prompts import chart_prompt

AGENT_KEY = "chart"

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
