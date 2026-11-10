"""report 的测试。"""

from eval_lite.models import Result
from eval_lite.report import to_csv, to_markdown


def make_results() -> list[Result]:
    return [
        Result(sample_id="q1", model="a", answer="巴黎", correct=True, latency_ms=100),
        Result(sample_id="q2", model="a", answer="伦敦", correct=False, latency_ms=200),
        Result(sample_id="q1", model="b", answer="巴黎", correct=True, latency_ms=150),
        Result(sample_id="q2", model="b", error="TimeoutError: 超时", latency_ms=30000),
    ]


def test_csv_has_one_row_per_result():
    lines = to_csv(make_results()).strip().splitlines()

    assert len(lines) == 1 + 4  # 表头 + 4 条结果


def test_markdown_has_a_row_per_model():
    md = to_markdown(make_results())

    assert "| a |" in md
    assert "| b |" in md


def test_failed_results_are_handled_consistently():
    """失败不算"答错"：b 的成功 1 条全对 → 100%，失败 1 条单独列。

    这个测试的价值是把"失败怎么算"这个设计决定**固定下来**。
    将来有人改了统计口径，测试会拦住他，逼他想清楚。
    """
    md = to_markdown(make_results())
    b_row = next(line for line in md.splitlines() if line.startswith("| b |"))
    cells = [c.strip() for c in b_row.strip("|").split("|")]

    assert cells[1] == "2"  # 样本数
    assert cells[2] == "1"  # 成功
    assert cells[3] == "1"  # 失败
    assert cells[4] == "100.0%"
