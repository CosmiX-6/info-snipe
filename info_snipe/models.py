from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Article:
    content_id: str
    title: str
    url: Optional[str]
    source_name: str
    genre: str
    description: Optional[str] = None
    published_at: Optional[datetime] = None
    image_url: Optional[str] = None
    country: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "content_id": self.content_id,
            "title": self.title,
            "url": self.url,
            "source_name": self.source_name,
            "genre": self.genre,
            "description": self.description,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "image_url": self.image_url,
            "country": self.country,
        }
