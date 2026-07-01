"""NewsAPI 기반 뉴스 수집 + Claude 기반 감성 분석 Tool."""

import datetime
import os

from utils.llm import call_llm_json
from utils.prompts import sentiment_prompt

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

SENTIMENT_FALLBACK = {"sentiment_score": 0.0, "summary": "감성 분석 실패, 중립으로 처리"}


class NewsDataTool:
    @staticmethod
    def get_news(ticker: str, company_name: str) -> list[dict]:
        if not NEWS_API_KEY:
            return []
        try:
            from newsapi import NewsApiClient

            client = NewsApiClient(api_key=NEWS_API_KEY)
            from_date = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
            query = company_name or ticker
            response = client.get_everything(
                q=query,
                from_param=from_date,
                language="en",
                sort_by="publishedAt",
                page_size=20,
            )
            articles = response.get("articles", [])
            return [
                {
                    "title": a.get("title"),
                    "description": a.get("description"),
                    "url": a.get("url"),
                    "published_at": a.get("publishedAt"),
                    "source": (a.get("source") or {}).get("name"),
                }
                for a in articles
            ]
        except Exception:  # noqa: BLE001
            return []

    @staticmethod
    def get_sentiment_score(news_list: list[dict], company_name: str = "") -> dict:
        if not news_list:
            return {"sentiment_score": 0.0, "summary": "최근 뉴스가 없어 중립으로 처리"}
        system_prompt, user_prompt = sentiment_prompt(news_list, company_name)
        return call_llm_json(system_prompt, user_prompt, SENTIMENT_FALLBACK)

    @classmethod
    def get_all(cls, ticker: str, company_name: str) -> dict:
        news_list = cls.get_news(ticker, company_name)
        sentiment = cls.get_sentiment_score(news_list, company_name)
        return {
            "articles": news_list,
            "sentiment": sentiment,
        }
