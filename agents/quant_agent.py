"""퀀트 Agent: 모멘텀/퀄리티/밸류/사이즈 팩터를 점수화해 종합 평가."""

from utils.llm import call_llm_json
from utils.prompts import quant_prompt

AGENT_KEY = "quant"

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
