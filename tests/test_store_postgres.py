import os
import uuid

import pytest

psycopg = pytest.importorskip("psycopg")

from info_snipe.models import Article
from info_snipe.store_postgres import PostgresContentStore

DATABASE_URL = os.environ.get("DATABASE_URL")

pytestmark = pytest.mark.skipif(
    not DATABASE_URL, reason="DATABASE_URL not set; skipping live Postgres tests"
)


@pytest.fixture
def store():
    namespace = f"test-{uuid.uuid4().hex[:12]}"
    s = PostgresContentStore(DATABASE_URL, namespace=namespace)
    yield s
    s._conn.execute("DELETE FROM seen_content WHERE namespace = %s", (namespace,))
    s.close()


def _article(content_id: str, genre: str = "tech") -> Article:
    return Article(
        content_id=content_id, title=f"Story {content_id}", url=f"https://example.com/{content_id}",
        source_name="Example", genre=genre,
    )


def test_mark_seen_and_has_seen(store):
    assert store.has_seen("abc") is False
    store.mark_seen(_article("abc"))
    assert store.has_seen("abc") is True


def test_filter_unseen(store):
    store.mark_seen(_article("a"))
    unseen = store.filter_unseen(["a", "b", "c"])
    assert unseen == {"b", "c"}


def test_mark_seen_many_is_idempotent(store):
    articles = [_article("x"), _article("y")]
    store.mark_seen_many(articles)
    store.mark_seen_many(articles)  # ON CONFLICT DO NOTHING must not raise
    assert store.count() == 2


def test_namespaces_are_isolated():
    ns_a = f"test-{uuid.uuid4().hex[:12]}"
    ns_b = f"test-{uuid.uuid4().hex[:12]}"
    store_a = PostgresContentStore(DATABASE_URL, namespace=ns_a)
    store_b = PostgresContentStore(DATABASE_URL, namespace=ns_b)
    try:
        store_a.mark_seen(_article("shared-id"))
        assert store_a.has_seen("shared-id") is True
        assert store_b.has_seen("shared-id") is False
    finally:
        store_a._conn.execute("DELETE FROM seen_content WHERE namespace = %s", (ns_a,))
        store_b._conn.execute("DELETE FROM seen_content WHERE namespace = %s", (ns_b,))
        store_a.close()
        store_b.close()


def test_count_scoped_by_genre(store):
    store.mark_seen(_article("t1", genre="tech"))
    store.mark_seen(_article("a1", genre="ai"))
    assert store.count() == 2
    assert store.count(genre="tech") == 1


def test_prune_older_than_recent_rows_not_pruned(store):
    store.mark_seen(_article("recent"))
    pruned = store.prune_older_than(days=30)
    assert pruned == 0
    assert store.has_seen("recent") is True
