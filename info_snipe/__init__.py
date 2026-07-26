import os
from typing import Optional, Union
from pathlib import Path

from .fetcher import NewsFetcher
from .genres import GenreConfig, get_genre, list_genres, register_genre
from .models import Article
from .sources.newsapi_source import NewsAPISource
from .sources.rss_source import RSSSource
from .store import ContentStore

__all__ = [
    "Article",
    "ContentStore",
    "NewsFetcher",
    "GenreConfig",
    "register_genre",
    "get_genre",
    "list_genres",
    "RSSSource",
    "NewsAPISource",
    "build_default_fetcher",
]


def build_default_fetcher(db_path: Optional[Union[str, Path]] = None) -> NewsFetcher:
    """Convenience factory: RSS is always included; NewsAPI is added
    automatically if the NEWSAPI_KEY environment variable is set."""
    sources = [RSSSource()]
    api_key = os.environ.get("NEWSAPI_KEY")
    if api_key:
        sources.append(NewsAPISource(api_key))
    store = ContentStore(db_path) if db_path else ContentStore()
    return NewsFetcher(sources=sources, store=store)
