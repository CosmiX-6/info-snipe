from typing import List, Optional

import requests

from ..genres import GenreConfig
from .base import NewsSource


class NewsAPISource(NewsSource):
    """Adapter for https://newsapi.org. Requires an API key."""

    name = "newsapi"
    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str, timeout: int = 10):
        if not api_key:
            raise ValueError("NewsAPISource requires a non-empty api_key")
        self.api_key = api_key
        self.timeout = timeout

    def fetch(self, genre: GenreConfig, country: Optional[str], limit: int) -> List[dict]:
        if genre.newsapi_category:
            endpoint = f"{self.BASE_URL}/top-headlines"
            params = {"category": genre.newsapi_category, "pageSize": min(limit, 100)}
            if country:
                params["country"] = country
        elif genre.newsapi_query:
            # /v2/everything has no country filter; topic-only genres rely on
            # RSS country feeds for regional coverage instead.
            endpoint = f"{self.BASE_URL}/everything"
            params = {
                "q": genre.newsapi_query,
                "pageSize": min(limit, 100),
                "sortBy": "publishedAt",
                "language": "en",
            }
        else:
            return []

        params["apiKey"] = self.api_key
        response = requests.get(endpoint, params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        articles = []
        for item in payload.get("articles", []):
            source = item.get("source") or {}
            articles.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "description": item.get("description"),
                    "source_name": source.get("name") or self.name,
                    "published_at": item.get("publishedAt"),
                    "image_url": item.get("urlToImage"),
                }
            )
        return articles
