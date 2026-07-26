from datetime import datetime, timezone
from time import mktime
from typing import List, Optional

import feedparser

from ..genres import GenreConfig
from .base import NewsSource


class RSSSource(NewsSource):
    """Adapter that reads a genre's configured RSS feeds. Needs no API key."""

    name = "rss"

    def fetch(self, genre: GenreConfig, country: Optional[str], limit: int) -> List[dict]:
        feed_urls = list(genre.rss_feeds)
        if country and country in genre.rss_feeds_by_country:
            feed_urls += genre.rss_feeds_by_country[country]

        articles = []
        for feed_url in feed_urls:
            parsed = feedparser.parse(feed_url)
            feed_title = parsed.feed.get("title", feed_url)
            for entry in parsed.entries[:limit]:
                articles.append(
                    {
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "description": entry.get("summary"),
                        "source_name": feed_title,
                        "published_at": _entry_published_at(entry),
                        "image_url": _entry_image(entry),
                    }
                )
        return articles


def _entry_published_at(entry) -> Optional[str]:
    parsed_time = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed_time:
        return None
    return datetime.fromtimestamp(mktime(parsed_time), tz=timezone.utc).isoformat()


def _entry_image(entry) -> Optional[str]:
    media_content = entry.get("media_content")
    if media_content:
        return media_content[0].get("url")
    return None
