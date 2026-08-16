from module import normalize_tag


def test_normalize_tag_strips_and_lowercases():
    assert normalize_tag("  Urgent  ") == "urgent"
