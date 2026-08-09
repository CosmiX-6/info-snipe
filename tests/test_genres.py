import pytest

from info_snipe.genres import GenreConfig, get_genre, list_genres, register_genre

BUILTIN_GENRES = {"ai", "tech", "world", "business", "science", "gaming"}


def test_builtin_genres_are_registered():
    assert BUILTIN_GENRES.issubset(set(list_genres()))


def test_gaming_genre_has_sources():
    genre = get_genre("gaming")
    assert genre.label == "Gaming"
    assert genre.rss_feeds
    assert genre.newsapi_query
    assert genre.newsapi_category is None


def test_get_genre_unknown_key_raises():
    with pytest.raises(KeyError):
        get_genre("not-a-real-genre")


def test_register_genre_rejects_duplicate_key_by_default():
    with pytest.raises(ValueError):
        register_genre(GenreConfig(key="gaming", label="Duplicate"))


def test_register_genre_allows_overwrite():
    register_genre(GenreConfig(key="gaming", label="Overwritten"), overwrite=True)
    try:
        assert get_genre("gaming").label == "Overwritten"
    finally:
        # restore the built-in definition so other tests aren't affected
        register_genre(
            GenreConfig(
                key="gaming",
                label="Gaming",
                newsapi_query='"video game" OR gaming',
                rss_feeds=["https://www.ign.com/rss/articles/feed"],
            ),
            overwrite=True,
        )
