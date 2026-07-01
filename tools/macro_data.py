"""FRED API 기반 매크로 지표 + Fear & Greed Index 수집 Tool.

FRED_API_KEY가 없거나 네트워크 오류가 발생해도 앱 전체가 죽지 않도록
모든 메서드는 실패 시 None/중립값과 note를 담은 dict를 반환한다.
"""

import os

import requests

FRED_API_KEY = os.getenv("FRED_API_KEY")
FEAR_GREED_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


class MacroDataTool:
    @staticmethod
    def get_interest_rates() -> dict:
        if not FRED_API_KEY:
            return {
                "fed_funds_rate": None,
                "treasury_10y": None,
                "note": "FRED_API_KEY가 설정되지 않아 금리 데이터를 가져오지 못했습니다.",
            }
        try:
            from fredapi import Fred

            fred = Fred(api_key=FRED_API_KEY)
            fed_funds = fred.get_series("FEDFUNDS").dropna().iloc[-1]
            treasury_10y = fred.get_series("DGS10").dropna().iloc[-1]
            return {
                "fed_funds_rate": float(fed_funds),
                "treasury_10y": float(treasury_10y),
            }
        except Exception as exc:  # noqa: BLE001
            return {"fed_funds_rate": None, "treasury_10y": None, "note": str(exc)}

    @staticmethod
    def get_dollar_index() -> dict:
        if not FRED_API_KEY:
            return {"dxy": None, "note": "FRED_API_KEY가 설정되지 않아 달러인덱스를 가져오지 못했습니다."}
        try:
            from fredapi import Fred

            fred = Fred(api_key=FRED_API_KEY)
            dxy = fred.get_series("DTWEXBGS").dropna().iloc[-1]
            return {"dxy": float(dxy)}
        except Exception as exc:  # noqa: BLE001
            return {"dxy": None, "note": str(exc)}

    @staticmethod
    def get_fear_greed() -> dict:
        try:
            resp = requests.get(
                FEAR_GREED_URL,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            score = data["fear_and_greed"]["score"]
            rating = data["fear_and_greed"]["rating"]
            return {"score": round(float(score)), "rating": rating}
        except Exception as exc:  # noqa: BLE001
            return {"score": 50, "rating": "중립", "note": f"조회 실패, 기본값 사용: {exc}"}

    @classmethod
    def get_all(cls) -> dict:
        return {
            "interest_rates": cls.get_interest_rates(),
            "dollar_index": cls.get_dollar_index(),
            "fear_greed": cls.get_fear_greed(),
        }
