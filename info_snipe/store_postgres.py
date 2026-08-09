from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional

from .models import Article

try:
    import psycopg
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "PostgresContentStore requires the 'postgres' extra: pip install info-snipe[postgres]"
    ) from exc


class PostgresContentStore:
    """Postgres-backed record of content-ids already fetched, mirroring
    ContentStore's method surface for serverless/multi-instance deployments
    where a local SQLite file can't persist across invocations.

    `namespace` scopes dedup to a caller-chosen partition (e.g. one per
    channel in a downstream app) so unrelated consumers of the same genre
    don't block each other's content. Defaults to "" (a single shared
    namespace), matching ContentStore's single-tenant behavior.
    """

    def __init__(self, dsn: str, namespace: str = ""):
        self.dsn = dsn
        self.namespace = namespace
        self._conn = psycopg.connect(dsn, autocommit=True)
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS seen_content (
                namespace TEXT NOT NULL DEFAULT '',
                content_id TEXT NOT NULL,
                genre TEXT NOT NULL,
                title TEXT,
                url TEXT,
                source_name TEXT,
                first_seen_at TIMESTAMPTZ NOT NULL,
                PRIMARY KEY (namespace, content_id)
            )
            """
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_seen_content_genre ON seen_content (namespace, genre)"
        )

    def has_seen(self, content_id: str) -> bool:
        cur = self._conn.execute(
            "SELECT 1 FROM seen_content WHERE namespace = %s AND content_id = %s",
            (self.namespace, content_id),
        )
        return cur.fetchone() is not None

    def filter_unseen(self, content_ids: Iterable[str]) -> set:
        ids = list(content_ids)
        if not ids:
            return set()
        cur = self._conn.execute(
            "SELECT content_id FROM seen_content WHERE namespace = %s AND content_id = ANY(%s)",
            (self.namespace, ids),
        )
        seen = {row[0] for row in cur.fetchall()}
        return set(ids) - seen

    def mark_seen(self, article: Article) -> None:
        self.mark_seen_many([article])

    def mark_seen_many(self, articles: Iterable[Article]) -> None:
        now = datetime.now(timezone.utc)
        rows = [
            (self.namespace, a.content_id, a.genre, a.title, a.url, a.source_name, now)
            for a in articles
        ]
        if not rows:
            return
        with self._conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO seen_content
                    (namespace, content_id, genre, title, url, source_name, first_seen_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (namespace, content_id) DO NOTHING
                """,
                rows,
            )

    def prune_older_than(self, days: int) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        cur = self._conn.execute(
            "DELETE FROM seen_content WHERE namespace = %s AND first_seen_at < %s",
            (self.namespace, cutoff),
        )
        return cur.rowcount

    def count(self, genre: Optional[str] = None) -> int:
        if genre:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM seen_content WHERE namespace = %s AND genre = %s",
                (self.namespace, genre),
            )
        else:
            cur = self._conn.execute(
                "SELECT COUNT(*) FROM seen_content WHERE namespace = %s", (self.namespace,)
            )
        return cur.fetchone()[0]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "PostgresContentStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
