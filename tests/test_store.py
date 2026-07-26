import pytest

from info_snipe.models import Article
from info_snipe.store import ContentStore


@pytest.fixture
def store(tmp_path):
    s = ContentStore(tmp_path / "test.db")
    yield s
    s.close()


def _article(content_id="abc123", genre="tech"):
    return Article(
        content_id=content_id,
        title="T",
        url="https://x.com",
        source_name="S",
        genre=genre,
    )


def test_filter_unseen_before_and_after_mark(store):
    assert store.filter_unseen(["abc123"]) == {"abc123"}
    store.mark_seen(_article())
    assert store.filter_unseen(["abc123"]) == set()


def test_mark_seen_many(store):
    articles = [_article(content_id=f"id{i}") for i in range(3)]
    store.mark_seen_many(articles)
    assert store.filter_unseen([a.content_id for a in articles]) == set()


def test_filter_unseen_empty_input(store):
    assert store.filter_unseen([]) == set()


def test_count_by_genre(store):
    store.mark_seen(_article(genre="tech"))
    assert store.count() == 1
    assert store.count(genre="tech") == 1
    assert store.count(genre="ai") == 0


def test_mark_seen_is_idempotent(store):
    article = _article()
    store.mark_seen(article)
    store.mark_seen(article)
    assert store.count() == 1
