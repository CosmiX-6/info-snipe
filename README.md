# info-snipe

[![GitHub repo](https://img.shields.io/badge/GitHub-CosmiX--6%2Finfo--snipe-181717?logo=github)](https://github.com/CosmiX-6/info-snipe)

Fetch de-duplicated news by genre/topic (AI, tech, world/global, gaming, …)
and country/region, from pluggable sources (RSS out of the box, NewsAPI.org
optionally). Every article gets a stable `content_id`, and a store remembers
which ids have already been returned so the same article is never handed back
twice. Two store backends ship out of the box:

- **SQLite** (default) — a local `~/.info_snipe/seen_content.db` file.
  Zero setup; works for single-process and local scripts.
- **Postgres** — a shared table that persists across serverless invocations
  and multiple processes. Use this when the fetcher runs in GitHub Actions,
  Vercel, or any other environment where the local filesystem is not durable.

## Install

```bash
pip install -e ".[dev]"          # SQLite only (default)
pip install -e ".[dev,postgres]" # also enables PostgresContentStore
```

Optionally set a NewsAPI.org key to enable that source in addition to RSS:

```bash
cp .env.example .env   # then fill in NEWSAPI_KEY, or export it directly
export NEWSAPI_KEY=your-key-here
```

RSS alone works with no key at all.

## How to use

### Basic (SQLite, default)

```python
from info_snipe import build_default_fetcher

fetcher = build_default_fetcher()

articles = fetcher.fetch(genre="ai", limit=10)
for a in articles:
    print(a.title, a.url)

# Run it again later and already-seen articles are skipped automatically:
more = fetcher.fetch(genre="ai", limit=10)  # only genuinely new articles

# Region-scoped:
uk_news = fetcher.fetch(genre="world", country="gb", limit=10)
```

Built-in genres: `ai`, `tech`, `world`, `business`, `science`, `gaming`
(`info_snipe.genres.list_genres()`).

### With Postgres (serverless / multi-instance)

```python
from info_snipe import NewsFetcher
from info_snipe.store_postgres import PostgresContentStore

store = PostgresContentStore(
    dsn="postgresql://user:pass@host/dbname",
    namespace="my-channel",   # scopes dedup; omit for a shared namespace
)

fetcher = NewsFetcher(store=store)
articles = fetcher.fetch(genre="tech", limit=5)
```

`PostgresContentStore` creates its own table (`seen_content`) on the first
connection — no manual migration needed. `namespace` lets multiple independent
callers share the same database without blocking each other's content (e.g.
one namespace per channel in a downstream app).

Use it as a context manager to close the connection cleanly:

```python
with PostgresContentStore("postgresql://...") as store:
    fetcher = NewsFetcher(store=store)
    articles = fetcher.fetch(genre="ai", limit=10)
```

Useful methods on `PostgresContentStore`:

| Method | What it does |
|---|---|
| `has_seen(content_id)` | True if this id was already marked seen |
| `mark_seen(article)` | Mark one article seen |
| `mark_seen_many(articles)` | Bulk mark; uses `ON CONFLICT DO NOTHING` |
| `prune_older_than(days)` | Delete records older than N days; returns count |
| `count(genre=None)` | Count records, optionally filtered by genre |

## CLI

```bash
info-snipe --genre ai --limit 10
info-snipe --genre world --country us --limit 5 --json
info-snipe --genre gaming --limit 5
```

## How dedup works

Each article is reduced to a `content_id`: a hash of its canonicalized URL
(scheme/`www.`/trailing-slash/tracking-params normalized), or of
`source+title` when a source has no URL. The store records every `content_id`
returned. `NewsFetcher.fetch()` dedupes both within a single call (e.g. the
same story appearing via RSS and NewsAPI) and against everything previously
marked seen. Pass `mark_seen=False` to preview results without recording them.

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

## Built-in genres

| Key | Topics covered | NewsAPI support |
|---|---|---|
| `ai` | Artificial intelligence, LLMs, ML research | ✓ (everything endpoint) |
| `tech` | Technology industry news | ✓ (top-headlines) |
| `world` | Global / international news | ✓ (top-headlines, country filter) |
| `business` | Business, markets, economy | ✓ (top-headlines) |
| `science` | Science, research, academia | ✓ (top-headlines) |
| `gaming` | Video games (IGN, Polygon, Kotaku, PC Gamer, Eurogamer) | ✓ (everything) |

## Notes / limitations

- Country filtering is native to NewsAPI's `top-headlines` endpoint (used by
  category-based genres like `tech`/`world`). Topic-only genres like `ai` use
  NewsAPI's `everything` endpoint, which has no country filter, so regional
  coverage for those relies on `rss_feeds_by_country` instead.
- Dedup is per identity (URL or source+title), so a story republished under a
  materially different URL by another outlet is treated as new content.
- `PostgresContentStore` requires `psycopg` (v3). Install with
  `pip install info-snipe[postgres]`.

## Tests

```bash
pytest
```
