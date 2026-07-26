import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable, Optional, Union

from .models import Article

DEFAULT_DB_PATH = Path.home() / ".info_snipe" / "seen_content.db"


class ContentStore:
    """SQLite-backed record of content-ids already fetched, so the same
    article is never returned twice across fetch() calls/runs."""

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS seen_content (
                    content_id TEXT PRIMARY KEY,
                    genre TEXT NOT NULL,
                    title TEXT,
                    url TEXT,
                    source_name TEXT,
                    first_seen_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_seen_genre ON seen_content(genre)")

    def has_seen(self, content_id: str) -> bool:
        cur = self._conn.execute("SELECT 1 FROM seen_content WHERE content_id = ?", (content_id,))
        return cur.fetchone() is not None

    def filter_unseen(self, content_ids: Iterable[str]) -> set:
        ids = list(content_ids)
        if not ids:
            return set()
        placeholders = ",".join("?" for _ in ids)
        cur = self._conn.execute(
            f"SELECT content_id FROM seen_content WHERE content_id IN ({placeholders})", ids
        )
        seen = {row[0] for row in cur.fetchall()}
        return set(ids) - seen

    def mark_seen(self, article: Article) -> None:
        self.mark_seen_many([article])

    def mark_seen_many(self, articles: Iterable[Article]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (a.content_id, a.genre, a.title, a.url, a.source_name, now) for a in articles
        ]
        if not rows:
            return
        with self._lock, self._conn:
            self._conn.executemany(
                """
                INSERT OR IGNORE INTO seen_content
                    (content_id, genre, title, url, source_name, first_seen_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

    def prune_older_than(self, days: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        with self._lock, self._conn:
            cur = self._conn.execute("DELETE FROM seen_content WHERE first_seen_at < ?", (cutoff,))
            return cur.rowcount

    def count(self, genre: Optional[str] = None) -> int:
        if genre:
            cur = self._conn.execute("SELECT COUNT(*) FROM seen_content WHERE genre = ?", (genre,))
        else:
            cur = self._conn.execute("SELECT COUNT(*) FROM seen_content")
        return cur.fetchone()[0]

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "ContentStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
