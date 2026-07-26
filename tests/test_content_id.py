from info_snipe.content_id import make_content_id


def test_tracking_params_and_trailing_slash_collapse_to_same_id():
    a = make_content_id(url="https://example.com/article?utm_source=x&utm_medium=y", title="T", source_name="S")
    b = make_content_id(url="https://www.example.com/article/", title="Different Title", source_name="S")
    assert a == b


def test_different_paths_yield_different_ids():
    a = make_content_id(url="https://example.com/a", title="T", source_name="S")
    b = make_content_id(url="https://example.com/b", title="T", source_name="S")
    assert a != b


def test_missing_url_falls_back_to_title_and_source_and_is_stable():
    a = make_content_id(url=None, title="Hello World", source_name="BBC")
    b = make_content_id(url=None, title="Hello World", source_name="BBC")
    assert a == b


def test_missing_url_different_source_yields_different_id():
    a = make_content_id(url=None, title="Hello World", source_name="BBC")
    b = make_content_id(url=None, title="Hello World", source_name="Reuters")
    assert a != b
