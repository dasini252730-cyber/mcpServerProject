"""각 Agent가 사용할 프롬프트 템플릿. 모든 함수는 (system_prompt, user_prompt) 튜플을 반환한다."""

import json


def _json_only(schema_desc: str) -> str:
    return (
        "\n\n반드시 아래 JSON 형식으로만 응답하세요. 설명 텍스트나 마크다운 코드블록 없이 "
        f"순수 JSON 객체만 출력하세요:\n{schema_desc}"
    )


def _dumps(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def value_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 20년 경력의 가치투자 전문 애널리스트입니다. PER, PBR, ROE, 영업이익률 등 "
        "재무 지표를 바탕으로 기업의 내재가치 대비 현재 주가의 적정성을 평가합니다. "
        "별도의 정량적 DCF 계산 데이터는 제공되지 않으므로, 주어진 재무 지표를 근거로 "
        "질적인 내재가치 판단을 내리세요."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})
사용자 질문: {state.get('question')}

[재무 데이터]
{_dumps(state.get('market_data', {}).get('financial', {}))}

판단 기준:
- PER이 업종 평균 대비 크게 높으면 고평가, 크게 낮으면 저평가로 판단
- PBR이 1 이하이면 저평가 신호
- ROE가 15% 이상이면 우량 기업으로 판단
- ROE 15% 이상 + PBR 1~3배 구간이면 우량주의 적정 범위로 판단
{_json_only('{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "상세 분석 3~5줄"}')}
"""
    return system, user


def quant_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 퀀트 애널리스트입니다. 모멘텀, 퀄리티, 밸류, 사이즈 팩터를 각각 0~25점으로 "
        "점수화하고 합산해 100점 만점으로 종합 평가합니다."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})

[재무 데이터]
{_dumps(state.get('market_data', {}).get('financial', {}))}

[모멘텀 데이터]
{_dumps(state.get('market_data', {}).get('momentum', {}))}

점수화 기준:
- 모멘텀 팩터(0~25점): 6개월 수익률이 높을수록 고득점
- 퀄리티 팩터(0~25점): ROE, 부채비율, 영업이익률이 좋을수록 고득점
- 밸류 팩터(0~25점): PER, PBR이 낮을수록 고득점
- 사이즈 팩터(0~25점): 시가총액 규모 고려
- 합산 70점 이상 매수, 40~70점 관망, 40점 미만 매도
{_json_only('{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "팩터별 점수 상세"}')}
"""
    return system, user


def macro_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 거시경제 분석 전문가입니다. 금리, 달러, 경기 사이클이 해당 종목/섹터에 "
        "유리한지 불리한지를 판단합니다."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})

[매크로 데이터]
{_dumps(state.get('macro_data', {}))}

판단 기준:
- 금리 인하 + 달러 약세는 성장주에 유리
- 금리 인상 국면은 가치주/배당주에 유리
- 경기 침체 신호가 있으면 방어주 선호
{_json_only('{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "매크로 환경 분석 3~5줄"}')}
"""
    return system, user


def chart_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 기술적 분석(차트) 전문가입니다. 이동평균선, RSI, MACD, 볼린저밴드를 "
        "바탕으로 단기 매매 타이밍을 판단합니다."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})

[차트 데이터]
{_dumps(state.get('chart_data', {}))}

판단 기준:
- 20일선 위 + RSI 50~70 + MACD 골든크로스면 매수
- RSI 70 초과 + 볼린저 상단 돌파면 단기 과매수로 관망
- 60일선 아래 + MACD 데드크로스면 매도
{_json_only('{"verdict": "매수|관망|매도", "score": 0~100 정수, "reason": "한 줄 요약", "detail": "차트 지표별 분석 3~5줄"}')}
"""
    return system, user


def risk_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 리스크 관리 전문가입니다. 베타, 최대낙폭(MDD), 변동성을 근거로 투자 "
        "위험도를 평가하고 최악의 시나리오를 제시합니다. score는 높을수록 리스크가 "
        "낮다는 의미입니다."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})

[변동성/리스크 데이터]
{_dumps(state.get('market_data', {}).get('volatility', {}))}

판단 기준:
- 베타 1.5 초과 + MDD 50% 초과면 고위험
- 베타 0.8~1.2 + MDD 30% 이하면 중위험
- 베타 0.8 미만이면 저위험
{_json_only(
    '{"verdict": "매수|관망|매도", "score": 0~100 정수(높을수록 저위험), '
    '"risk_level": "고위험|중위험|저위험", "worst_case": "최악 시나리오 한 줄", '
    '"reason": "한 줄 요약", "detail": "리스크 요인 상세"}'
)}
"""
    return system, user


def behavioral_prompt(state: dict) -> tuple[str, str]:
    system = (
        "당신은 행동경제학/시장심리 전문가입니다. 뉴스 감성, Fear & Greed Index, 군중 "
        "행동 패턴을 바탕으로 역발상 투자 신호를 판단합니다."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})

[뉴스 감성 및 심리 데이터]
{_dumps(state.get('news_data', {}))}

[Fear & Greed / 매크로 심리 데이터]
{_dumps(state.get('macro_data', {}).get('fear_greed', {}))}

판단 기준:
- Fear & Greed 80 이상(극도의 탐욕)이면 역발상 매도 신호
- Fear & Greed 20 이하(극도의 공포)면 역발상 매수 신호
- 뉴스 감성이 +0.8 이상으로 과열되어 있으면 이미 호재가 반영된 것으로 보고 관망
- 뉴스 감성이 -0.6 이하로 악화되어 있으면 과매도 가능성을 보고 저점 주시
{_json_only(
    '{"verdict": "매수|관망|매도", "score": 0~100 정수, '
    '"market_emotion": "극도의 탐욕|탐욕|중립|공포|극도의 공포", '
    '"contrarian_signal": true 또는 false, "reason": "한 줄 요약", "detail": "심리 지표 분석 3~5줄"}'
)}
"""
    return system, user


def orchestrator_prompt(
    state: dict, final_verdict: str, final_score: float, confidence: str
) -> tuple[str, str]:
    system = (
        "당신은 6명의 전문가 의견을 종합하는 수석 투자 전략가입니다. 이미 계산된 최종 "
        "판단과 점수를 근거로, 그 판단에 이르게 된 핵심 이유를 설명하고 소수 의견이 "
        "있다면 함께 요약하세요."
    )
    user = f"""종목: {state.get('company_name')} ({state.get('ticker')})
사용자 질문: {state.get('question')}

[6개 Agent 의견]
{_dumps(state.get('opinions', {}))}

[가중치 기반 계산 결과 - 이미 확정됨, 재계산하지 마세요]
- 최종 판단: {final_verdict}
- 가중 평균 점수: {final_score:.1f}
- 신뢰도: {confidence}

위 결과에 이르게 된 핵심 근거를 2~3줄로 요약하고, 최종 판단과 다른 소수 의견이 있다면 한 줄로 요약하세요. 소수 의견이 없다면 빈 문자열로 두세요.
{_json_only('{"key_reason": "핵심 판단 근거 2~3줄", "dissenting_opinion": "소수 의견 요약 또는 빈 문자열"}')}
"""
    return system, user


def sentiment_prompt(news_list: list, company_name: str) -> tuple[str, str]:
    system = (
        "당신은 금융 뉴스 감성 분석 전문가입니다. 뉴스 헤드라인과 요약을 읽고 "
        "해당 종목에 대한 시장 감성을 -1(매우 부정)에서 +1(매우 긍정) 사이 점수로 평가합니다."
    )
    headlines = "\n".join(
        f"- {item.get('title', '')}: {item.get('description', '')}" for item in news_list
    )
    user = f"""종목: {company_name}

[최근 뉴스 헤드라인]
{headlines if headlines else '(뉴스 없음)'}
{_json_only('{"sentiment_score": -1.0~1.0 사이 실수, "summary": "감성 분석 요약 한 줄"}')}
"""
    return system, user
