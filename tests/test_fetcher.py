from info_snipe.fetcher import NewsFetcher
from info_snipe.sources.base import NewsSource
from info_snipe.store import ContentStore


class FakeSource(NewsSource):
    name = "fake"

    def __init__(self, items):
        self.items = items

    def fetch(self, genre, country, limit):
        return self.items


class BrokenSource(NewsSource):
    name = "broken"

    def fetch(self, genre, country, limit):
        raise RuntimeError("network is down")


def make_item(i, url=None):
    return {
        "title": f"Article {i}",
        "url": url or f"https://example.com/{i}",
        "description": "desc",
        "source_name": "FakeSrc",
        "published_at": "2024-01-01T00:00:00Z",
        "image_url": None,
    }


def test_fetch_dedupes_across_calls(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    source = FakeSource([make_item(1), make_item(2)])
    fetcher = NewsFetcher(sources=[source], store=store)

    first = fetcher.fetch(genre="ai", limit=10)
    assert len(first) == 2

    second = fetcher.fetch(genre="ai", limit=10)
    assert second == []


def test_fetch_dedupes_within_batch_across_sources(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    item = make_item(1)
    fetcher = NewsFetcher(sources=[FakeSource([item]), FakeSource([item])], store=store)

    result = fetcher.fetch(genre="ai", limit=10)
    assert len(result) == 1


def test_mark_seen_false_does_not_persist(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    fetcher = NewsFetcher(sources=[FakeSource([make_item(1)])], store=store)

    fetcher.fetch(genre="ai", limit=10, mark_seen=False)
    second = fetcher.fetch(genre="ai", limit=10)
    assert len(second) == 1


def test_items_missing_title_or_url_are_skipped(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    items = [
        {"title": "", "url": "https://example.com/1", "source_name": "S", "published_at": None, "description": None, "image_url": None},
        {"title": "No URL", "url": None, "source_name": "S", "published_at": None, "description": None, "image_url": None},
        make_item(2),
    ]
    fetcher = NewsFetcher(sources=[FakeSource(items)], store=store)

    result = fetcher.fetch(genre="ai", limit=10)
    assert len(result) == 1
    assert result[0].title == "Article 2"


def test_broken_source_does_not_break_fetch(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    fetcher = NewsFetcher(sources=[BrokenSource(), FakeSource([make_item(1)])], store=store)

    result = fetcher.fetch(genre="ai", limit=10)
    assert len(result) == 1


def test_limit_is_respected(tmp_path):
    store = ContentStore(tmp_path / "t.db")
    items = [make_item(i) for i in range(5)]
    fetcher = NewsFetcher(sources=[FakeSource(items)], store=store)

    result = fetcher.fetch(genre="ai", limit=2)
    assert len(result) == 2
