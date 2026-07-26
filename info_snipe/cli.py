import argparse
import json
import sys
from typing import Optional, Sequence

from . import build_default_fetcher
from .genres import list_genres


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="info-snipe", description="Fetch de-duplicated news by genre and country/region."
    )
    parser.add_argument("--genre", required=True, choices=list_genres(), help="News genre/topic to fetch")
    parser.add_argument("--country", default=None, help="ISO 3166-1 alpha-2 country code, e.g. us, gb, in")
    parser.add_argument("--limit", type=int, default=10, help="Max number of articles to return")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--no-mark-seen", action="store_true", help="Don't record fetched articles as seen"
    )
    args = parser.parse_args(argv)

    fetcher = build_default_fetcher()
    articles = fetcher.fetch(
        genre=args.genre,
        country=args.country,
        limit=args.limit,
        mark_seen=not args.no_mark_seen,
    )

    if args.json:
        print(json.dumps([a.to_dict() for a in articles], indent=2))
    elif not articles:
        print("No new articles found.")
    else:
        for article in articles:
            print(f"- [{article.source_name}] {article.title}\n  {article.url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
