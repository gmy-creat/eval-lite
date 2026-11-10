"""metrics 的测试。"""

import pytest

from eval_lite.metrics import accuracy, contains_match, exact_match, normalize


def test_normalize_strips_and_lowercases():
    assert normalize("  Paris.  ") == "paris"


def test_normalize_collapses_whitespace():
    assert normalize("a     b") == "a b"


def test_exact_match_ignores_trailing_punctuation():
    assert exact_match("巴黎。", "巴黎") is True
    assert exact_match("伦敦", "巴黎") is False


def test_contains_match_is_looser():
    assert contains_match("答案是巴黎。", "巴黎") is True


def test_accuracy_raises_on_empty():
    with pytest.raises(ValueError, match="为空"):
        accuracy([])


def test_accuracy_basic():
    assert accuracy([True, True, False, True]) == 0.75
