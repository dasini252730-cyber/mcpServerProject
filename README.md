# StockMind — 멀티에이전트 주식 분석기

종목명을 입력하면 6개의 전문 AI Agent(가치투자·퀀트·매크로·차트·리스크·행동경제학)가
각자 다른 관점에서 분석하고, Orchestrator Agent가 가중치 기반으로 종합해
매수 / 관망 / 매도 판단을 제시하는 LangGraph 기반 Streamlit 앱입니다.

## 디렉토리 구조

```
stockmind/
├── app.py                    # Streamlit 메인 앱
├── requirements.txt
├── .env.example
├── agents/                   # 6개 분석 Agent + Orchestrator
├── tools/                    # 데이터 수집 (yfinance, FRED, NewsAPI, ta)
├── graph/                    # LangGraph State/Workflow
└── utils/                    # 프롬프트 템플릿, 리포트 포맷터, LLM 헬퍼
```

## 분석 흐름

```
데이터 수집
  → 6개 Agent 1차 독립 분석 (병렬)
  → 6개 Agent 동료 의견 반영 재검토 (각자 나머지 5명의 1차 의견을 보고 유지/수정)
  → Orchestrator 가중 종합
  → 리포트 생성
```

1차 라운드는 서로의 의견을 모른 채 독립적으로 분석해 관점의 다양성을 확보하고,
2차 라운드에서 각 Agent가 동료들의 1차 의견을 참고해 자신의 판단을 유지하거나
조정합니다. Orchestrator는 이 재검토된(2차) 의견을 바탕으로 최종 판단을 내립니다.
(Agent당 LLM 호출이 1차+2차로 2회씩 발생해 API 비용이 기존 대비 약 2배입니다.)

Orchestrator는 각 Agent의 0~100점 점수를 다음 가중치로 평균해 최종 점수를 냅니다:

| Agent | 가중치 |
|---|---|
| 리스크 | 1.5 |
| 퀀트 | 1.3 |
| 가치투자 | 1.2 |
| 매크로 | 1.0 |
| 행동경제학 | 0.9 |
| 차트 | 0.8 |

최종 점수 65점 이상 매수, 40~65점 관망, 40점 미만 매도로 판단합니다.

## 설치 및 실행

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# .env 파일을 열어 API 키를 입력하세요

streamlit run app.py
```

## 환경 변수

| 변수 | 필수 여부 | 설명 |
|---|---|---|
| `ANTHROPIC_API_KEY` | 필수 | 6개 Agent + Orchestrator가 사용하는 Claude API 키 |
| `NEWS_API_KEY` | 선택 | 없으면 뉴스/감성 분석이 중립값으로 처리됩니다 ([newsapi.org](https://newsapi.org) 무료 가입) |
| `FRED_API_KEY` | 선택 | 없으면 금리/달러인덱스가 조회되지 않습니다 ([fred.stlouisfed.org](https://fred.stlouisfed.org) 무료 가입) |
| `ANTHROPIC_MODEL` | 선택 | 기본값 `claude-sonnet-5` |

Fear & Greed Index는 별도 API 키 없이 공개 엔드포인트를 조회하며, 실패 시 중립값(50)으로 대체됩니다.

## 알려진 단순화

- 가치투자 Agent는 정량적 DCF 계산 대신 PER/PBR/ROE 등 재무 지표를 근거로 LLM이 질적 내재가치 판단을 내립니다.
- 공매도 비율 데이터는 무료로 안정적인 소스가 없어 리스크 Agent에서 제외했습니다 (베타/MDD/변동성으로 대체).

## Streamlit Cloud 배포

1. GitHub에 리포지토리를 push합니다.
2. [streamlit.io](https://streamlit.io) → New app → GitHub 리포지토리 연결
3. App 설정에서 `app.py`를 엔트리포인트로 지정
4. Settings → Secrets에 아래처럼 **TOML 형식**으로 입력 (`.env`의 `KEY=value` 형식이 아니라 값에 따옴표가 필요합니다):

   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   NEWS_API_KEY = "..."
   FRED_API_KEY = "..."
   ANTHROPIC_MODEL = "claude-sonnet-5"
   ```

5. Deploy

## 면책 고지

본 분석은 참고용이며, 실제 투자 결정과 그에 따른 책임은 전적으로 사용자 본인에게 있습니다.
