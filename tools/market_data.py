"""yfinance 기반 주가/재무 데이터 수집 Tool."""

import numpy as np
import yfinance as yf

from tools.yf_session import fetch_with_retry, get_session


def _ticker(ticker: str) -> yf.Ticker:
    return yf.Ticker(ticker, session=get_session())


class MarketDataTool:
    @staticmethod
    def get_price_data(info: dict) -> dict:
        return {
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "week52_high": info.get("fiftyTwoWeekHigh"),
            "week52_low": info.get("fiftyTwoWeekLow"),
            "volume": info.get("volume") or info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "currency": info.get("currency"),
        }

    @staticmethod
    def get_financial_data(info: dict) -> dict:
        return {
            "per": info.get("trailingPE"),
            "pbr": info.get("priceToBook"),
            "roe": info.get("returnOnEquity"),
            "eps": info.get("trailingEps"),
            "operating_margin": info.get("operatingMargins"),
            "debt_to_equity": info.get("debtToEquity"),
        }

    @staticmethod
    def get_momentum_data(hist) -> dict:
        if hist.empty:
            return {"return_1m": None, "return_3m": None, "return_6m": None, "return_1y": None}

        close = hist["Close"]

        def _return_over(days: int):
            if len(close) <= days:
                return None
            return float(close.iloc[-1] / close.iloc[-days - 1] - 1)

        return {
            "return_1m": _return_over(21),
            "return_3m": _return_over(63),
            "return_6m": _return_over(126),
            "return_1y": _return_over(251),
        }

    @staticmethod
    def get_volatility_data(info: dict, hist) -> dict:
        if hist.empty:
            return {"beta": info.get("beta"), "std_dev": None, "mdd": None}

        daily_returns = hist["Close"].pct_change().dropna()
        std_dev = float(daily_returns.std() * np.sqrt(252)) if not daily_returns.empty else None

        cumulative = (1 + daily_returns).cumprod()
        running_max = cumulative.cummax()
        drawdown = cumulative / running_max - 1
        mdd = float(drawdown.min()) if not drawdown.empty else None

        return {
            "beta": info.get("beta"),
            "std_dev": std_dev,
            "mdd": mdd,
        }

    @classmethod
    def get_all(cls, ticker: str) -> dict:
        # Yahoo Finance의 rate limit을 피하기 위해 info/history를 한 번씩만 조회해 공유하고,
        # 일시적인 rate limit에는 짧게 재시도한다.
        t = _ticker(ticker)
        info = fetch_with_retry(lambda: t.info)
        hist = fetch_with_retry(lambda: t.history(period="1y"))
        return {
            "price": cls.get_price_data(info),
            "financial": cls.get_financial_data(info),
            "momentum": cls.get_momentum_data(hist),
            "volatility": cls.get_volatility_data(info, hist),
        }
