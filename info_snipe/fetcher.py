from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Union

from dateutil import parser as dateutil_parser

from .content_id import make_content_id
from .genres import GenreConfig, get_genre
from .models import Article
from .sources.base import NewsSource
from .store import ContentStore

_MIN_DATETIME = datetime.min.replace(tzinfo=timezone.utc)


class NewsFetcher:
    """Orchestrates one or more NewsSources for a genre, normalizes their
    output into Articles, and filters out anything already seen."""

    def __init__(self, sources: Sequence[NewsSource], store: Optional[ContentStore] = None):
        if not sources:
            raise ValueError("NewsFetcher requires at least one NewsSource")
        self.sources = list(sources)
        self.store = store or ContentStore()

    def fetch(
        self,
        genre: Union[str, GenreConfig],
        country: Optional[str] = None,
        limit: int = 20,
        mark_seen: bool = True,
    ) -> List[Article]:
        genre_config = get_genre(genre) if isinstance(genre, str) else genre

        candidates: Dict[str, Article] = {}
        for source in self.sources:
            try:
                raw_items = source.fetch(genre_config, country, limit)
            except Exception:
                # A single misbehaving source shouldn't fail the whole fetch.
                continue
            for item in raw_items:
                article = _normalize(item, genre_config.key, country, source.name)
                if article and article.content_id not in candidates:
                    candidates[article.content_id] = article

        unseen_ids = self.store.filter_unseen(candidates.keys())
        fresh_articles = [article for cid, article in candidates.items() if cid in unseen_ids]
        fresh_articles.sort(key=lambda a: a.published_at or _MIN_DATETIME, reverse=True)
        fresh_articles = fresh_articles[:limit]

        if mark_seen and fresh_articles:
            self.store.mark_seen_many(fresh_articles)

        return fresh_articles


def _normalize(item: dict, genre_key: str, country: Optional[str], source_name: str) -> Optional[Article]:
    title = (item.get("title") or "").strip()
    url = item.get("url")
    if not title or not url:
        return None
    resolved_source = item.get("source_name") or source_name
    content_id = make_content_id(url=url, title=title, source_name=resolved_source)
    return Article(
        content_id=content_id,
        title=title,
        url=url,
        description=item.get("description"),
        source_name=resolved_source,
        genre=genre_key,
        published_at=_parse_datetime(item.get("published_at")),
        image_url=item.get("image_url"),
        country=country,
    )


def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = dateutil_parser.parse(value)
    except (ValueError, TypeError):
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
