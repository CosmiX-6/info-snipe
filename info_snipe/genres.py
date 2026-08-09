from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class GenreConfig:
    key: str
    label: str
    # For NewsAPI's /v2/everything endpoint (free-text topic search).
    newsapi_query: Optional[str] = None
    # For NewsAPI's /v2/top-headlines endpoint (category + optional country).
    newsapi_category: Optional[str] = None
    # RSS feeds queried regardless of country.
    rss_feeds: List[str] = field(default_factory=list)
    # Extra RSS feeds added when a matching country code is requested.
    rss_feeds_by_country: Dict[str, List[str]] = field(default_factory=dict)


_GENRES: Dict[str, GenreConfig] = {}


def register_genre(genre: GenreConfig, overwrite: bool = False) -> None:
    if not overwrite and genre.key in _GENRES:
        raise ValueError(f"Genre '{genre.key}' is already registered")
    _GENRES[genre.key] = genre


def get_genre(key: str) -> GenreConfig:
    try:
        return _GENRES[key]
    except KeyError:
        raise KeyError(f"Unknown genre '{key}'. Available genres: {sorted(_GENRES)}") from None


def list_genres() -> List[str]:
    return sorted(_GENRES)


# --- built-in genres -------------------------------------------------------

register_genre(
    GenreConfig(
        key="ai",
        label="Artificial Intelligence",
        newsapi_query=(
            '"artificial intelligence" OR "machine learning" OR LLM OR '
            'ChatGPT OR "AI tools" OR "AI model"'
        ),
        rss_feeds=[
            "https://www.artificialintelligence-news.com/feed/",
            "https://techcrunch.com/tag/artificial-intelligence/feed/",
            "https://www.technologyreview.com/feed/",
            "https://venturebeat.com/category/ai/feed/",
        ],
    )
)

register_genre(
    GenreConfig(
        key="tech",
        label="Technology & Gadgets",
        newsapi_category="technology",
        rss_feeds=[
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://arstechnica.com/feed/",
        ],
    )
)

register_genre(
    GenreConfig(
        key="world",
        label="Global / World News",
        newsapi_category="general",
        rss_feeds=[
            "http://feeds.bbci.co.uk/news/world/rss.xml",
            "https://www.aljazeera.com/xml/rss/all.xml",
        ],
        rss_feeds_by_country={
            "us": ["https://feeds.npr.org/1004/rss.xml"],
            "gb": ["http://feeds.bbci.co.uk/news/uk/rss.xml"],
            "in": ["https://www.thehindu.com/news/national/feeder/default.rss"],
        },
    )
)

register_genre(
    GenreConfig(
        key="business",
        label="Business & Finance",
        newsapi_category="business",
        rss_feeds=["https://feeds.a.dj.com/rss/RSSMarketsMain.xml"],
    )
)

register_genre(
    GenreConfig(
        key="science",
        label="Science",
        newsapi_category="science",
        rss_feeds=["https://www.sciencedaily.com/rss/all.xml"],
    )
)

register_genre(
    GenreConfig(
        key="gaming",
        label="Gaming",
        # NewsAPI has no top-headlines "gaming" category, so this genre
        # relies on /v2/everything free-text search instead (same pattern
        # as "ai").
        newsapi_query=(
            '"video game" OR gaming OR esports OR PlayStation OR Xbox OR '
            'Nintendo OR "PC gaming"'
        ),
        rss_feeds=[
            "https://www.ign.com/rss/articles/feed",
            "https://www.polygon.com/rss/index.xml",
            "https://kotaku.com/rss",
            "https://www.pcgamer.com/rss/",
            "https://www.eurogamer.net/feed",
        ],
    )
)
