"""Claude API 호출 공통 헬퍼. 각 Agent가 동일한 방식으로 LLM을 호출하고
JSON 형태의 응답을 파싱할 수 있도록 한다."""

import json
import os
import re

from langchain_anthropic import ChatAnthropic

DEFAULT_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")


def get_llm(temperature: float = 0.3, max_tokens: int = 1024) -> ChatAnthropic:
    return ChatAnthropic(
        model=DEFAULT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def _extract_json(text: str) -> dict:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("LLM 응답에서 JSON 객체를 찾지 못했습니다.")
    return json.loads(match.group(0))


def call_llm_json(system_prompt: str, user_prompt: str, fallback: dict) -> dict:
    """LLM을 호출해 JSON 딕셔너리를 반환한다. 실패 시 fallback에 에러 메시지를 담아 반환한다."""
    try:
        llm = get_llm()
        response = llm.invoke(
            [
                ("system", system_prompt),
                ("human", user_prompt),
            ]
        )
        return _extract_json(response.content)
    except Exception as exc:  # noqa: BLE001 - 개별 Agent 실패가 전체 흐름을 막지 않도록 함
        result = dict(fallback)
        result["error"] = str(exc)
        return result
