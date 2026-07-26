# info-snipe

[![GitHub repo](https://img.shields.io/badge/GitHub-CosmiX--6%2Finfo--snipe-181717?logo=github)](https://github.com/CosmiX-6/info-snipe)

Fetch de-duplicated news by genre/topic (AI, tech, world/global, ...) and
country/region, from pluggable sources (RSS out of the box, NewsAPI.org
optionally). Every article gets a stable `content_id`, and a local SQLite
store remembers which ids have already been returned so the same article is
never handed back twice.

## Install

```bash
pip install -e ".[dev]"
```

Optionally set a NewsAPI.org key to enable that source in addition to RSS:

```bash
cp .env.example .env   # then fill in NEWSAPI_KEY, or export it directly
export NEWSAPI_KEY=your-key-here
```

RSS alone works with no key at all.

## Quickstart (library)

```python
from info_snipe import build_default_fetcher

fetcher = build_default_fetcher()

articles = fetcher.fetch(genre="ai", limit=10)
for a in articles:
    print(a.title, a.url)

# Run it again later/elsewhere and already-seen articles are skipped:
more = fetcher.fetch(genre="ai", limit=10)  # only genuinely new articles

# Region-scoped:
uk_news = fetcher.fetch(genre="world", country="gb", limit=10)
```

Built-in genres: `ai`, `tech`, `world`, `business`, `science`
(`info_snipe.genres.list_genres()`).

## CLI

```bash
info-snipe --genre ai --limit 10
info-snipe --genre world --country us --limit 5 --json
```

## How dedup works

Each article is reduced to a `content_id`: a hash of its canonicalized URL
(scheme/`www.`/trailing-slash/tracking-params normalized), or of
`source+title` when a source has no URL. A SQLite file at
`~/.info_snipe/seen_content.db` (override via `ContentStore(db_path=...)` or
`build_default_fetcher(db_path=...)`) records every `content_id` returned.
`NewsFetcher.fetch()` dedupes both within a single call (e.g. the same story
appearing via RSS and NewsAPI) and against everything previously marked
seen. Pass `mark_seen=False` to preview results without recording them.

## Adding a genre

```python
from info_snipe import register_genre, GenreConfig

register_genre(GenreConfig(
    key="sports",
    label="Sports",
    newsapi_category="sports",
    rss_feeds=["https://example.com/sports/feed"],
))
```

## Adding a source

Implement `info_snipe.sources.base.NewsSource`:

```python
class MySource(NewsSource):
    name = "my_source"

    def fetch(self, genre, country, limit):
        # return a list of dicts: title, url, description, source_name,
        # published_at (ISO string or None), image_url
        ...
```

Pass an instance into `NewsFetcher(sources=[...])`.

## Notes / limitations

- Country filtering is native to NewsAPI's `top-headlines` endpoint (used by
  category-based genres like `tech`/`world`). Topic-only genres like `ai`
  use NewsAPI's `everything` endpoint, which has no country filter, so regional
  coverage for those relies on `rss_feeds_by_country` instead.
- Dedup is per identity (URL or source+title), so a story republished under a
  materially different URL by another outlet is treated as new content.

## Tests

```bash
pytest
```
