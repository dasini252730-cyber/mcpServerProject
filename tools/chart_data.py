"""ta 라이브러리 기반 기술적 지표 계산 Tool."""

import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import MACD, SMAIndicator
from ta.volatility import BollingerBands

from tools.yf_session import get_session


def _history(ticker: str):
    return yf.Ticker(ticker, session=get_session()).history(period="1y")


class ChartDataTool:
    @staticmethod
    def get_moving_averages(hist) -> dict:
        if hist.empty:
            return {}

        close = hist["Close"]
        current_price = float(close.iloc[-1])
        result = {"current_price": current_price}
        for window in (5, 20, 60, 120):
            if len(close) >= window:
                ma = SMAIndicator(close, window=window).sma_indicator().iloc[-1]
                result[f"ma{window}"] = float(ma)
            else:
                result[f"ma{window}"] = None

        result["position_vs_ma20"] = (
            "위" if result.get("ma20") and current_price > result["ma20"] else "아래"
        )
        result["position_vs_ma60"] = (
            "위" if result.get("ma60") and current_price > result["ma60"] else "아래"
        )
        return result

    @staticmethod
    def get_rsi(hist) -> dict:
        if hist.empty or len(hist) < 15:
            return {"rsi": None, "signal": "데이터 부족"}

        rsi_value = float(RSIIndicator(hist["Close"], window=14).rsi().iloc[-1])
        if rsi_value >= 70:
            signal = "과매수"
        elif rsi_value <= 30:
            signal = "과매도"
        else:
            signal = "중립"
        return {"rsi": rsi_value, "signal": signal}

    @staticmethod
    def get_macd(hist) -> dict:
        if hist.empty or len(hist) < 35:
            return {"macd": None, "signal_line": None, "histogram": None, "cross": "데이터 부족"}

        macd_ind = MACD(hist["Close"], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd_ind.macd()
        signal_line = macd_ind.macd_signal()
        histogram = macd_ind.macd_diff()

        prev_diff = float(histogram.iloc[-2])
        curr_diff = float(histogram.iloc[-1])
        if prev_diff <= 0 < curr_diff:
            cross = "골든크로스"
        elif prev_diff >= 0 > curr_diff:
            cross = "데드크로스"
        else:
            cross = "크로스 없음"

        return {
            "macd": float(macd_line.iloc[-1]),
            "signal_line": float(signal_line.iloc[-1]),
            "histogram": curr_diff,
            "cross": cross,
        }

    @staticmethod
    def get_bollinger_bands(hist) -> dict:
        if hist.empty or len(hist) < 20:
            return {"upper": None, "mid": None, "lower": None, "position": "데이터 부족"}

        bb = BollingerBands(hist["Close"], window=20, window_dev=2)
        upper = float(bb.bollinger_hband().iloc[-1])
        mid = float(bb.bollinger_mavg().iloc[-1])
        lower = float(bb.bollinger_lband().iloc[-1])
        current_price = float(hist["Close"].iloc[-1])

        if current_price > upper:
            position = "상단 돌파(과매수)"
        elif current_price < lower:
            position = "하단 이탈(과매도)"
        else:
            position = "밴드 내부"

        return {"upper": upper, "mid": mid, "lower": lower, "position": position}

    @classmethod
    def get_all(cls, ticker: str) -> dict:
        # Yahoo Finance의 rate limit을 피하기 위해 history를 한 번만 조회해 공유한다.
        hist = _history(ticker)
        return {
            "moving_averages": cls.get_moving_averages(hist),
            "rsi": cls.get_rsi(hist),
            "macd": cls.get_macd(hist),
            "bollinger_bands": cls.get_bollinger_bands(hist),
        }
