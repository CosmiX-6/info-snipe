from abc import ABC, abstractmethod
from typing import List, Optional

from ..genres import GenreConfig


class NewsSource(ABC):
    """A pluggable news provider. Implementations fetch raw articles for a
    genre and return them as plain dicts with keys: title, url, description,
    source_name, published_at (ISO string or None), image_url."""

    name: str

    @abstractmethod
    def fetch(self, genre: GenreConfig, country: Optional[str], limit: int) -> List[dict]:
        raise NotImplementedError
