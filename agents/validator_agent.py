"""검증 Agent: 각 Agent의 판단이 실제 근거 데이터에 기반하는지 확인한다.

근거 데이터가 아예 없는데도(데이터 수집 실패 등) 확신에 찬 "관망/매수/매도"를
내놓는 걸 막기 위한 안전장치. 두 단계로 검증한다:

1. 결정적(deterministic) 체크: 해당 Agent의 근거 데이터가 비어있거나 LLM 호출
   자체가 실패했다면, LLM에게 물어볼 것도 없이 grounded=False로 확정한다.
2. 근거 데이터가 있는 나머지 Agent에 한해서만, reason/detail이 실제로 그 데이터와
   앞뒤가 맞는지 LLM 한 번으로 교차 검증한다 (Agent마다 호출하지 않고 묶어서 1회).
"""

from utils.formatter import AGENT_ORDER, agent_evidence
from utils.llm import call_llm_json
from utils.prompts import validation_prompt

NO_EVIDENCE_NOTE = "근거 데이터가 없거나 LLM 호출이 실패해 신뢰할 수 없는 판단입니다."


def _has_content(value) -> bool:
    if isinstance(value, dict):
        return any(_has_content(v) for v in value.values())
    return value not in (None, "", [])


def validate(state: dict) -> dict:
    opinions = state.get("opinions", {})
    evidence = agent_evidence(state)

    validation = {}
    needs_llm_check = {}

    for key in AGENT_ORDER:
        op = opinions.get(key)
        if not op:
            continue
        if op.get("error") or not _has_content(evidence.get(key, {})):
            validation[key] = {"grounded": False, "note": NO_EVIDENCE_NOTE}
        else:
            needs_llm_check[key] = {"opinion": op, "evidence": evidence.get(key, {})}

    if needs_llm_check:
        system_prompt, user_prompt = validation_prompt(needs_llm_check)
        fallback = {key: {"grounded": True, "note": ""} for key in needs_llm_check}
        llm_result = call_llm_json(system_prompt, user_prompt, fallback)
        for key in needs_llm_check:
            result = llm_result.get(key)
            if isinstance(result, dict) and "grounded" in result:
                validation[key] = {
                    "grounded": bool(result.get("grounded")),
                    "note": result.get("note", ""),
                }
            else:
                validation[key] = fallback[key]

    return {"validation": validation}
