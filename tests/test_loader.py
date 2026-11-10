"""loader 的测试。"""

import pytest

from eval_lite.loader import SampleFormatError, load_samples


def test_loads_all_samples(sample_qa_file):
    samples = load_samples(sample_qa_file)

    assert [s.id for s in samples] == ["q1", "q2", "q3"]
    assert samples[0].reference == "巴黎"


def test_skips_blank_lines(tmp_path):
    path = tmp_path / "qa.jsonl"
    path.write_text(
        '{"id": "q1", "prompt": "第一条"}\n\n   \n{"id": "q2", "prompt": "第二条"}\n',
        encoding="utf-8",
    )

    samples = load_samples(path)

    assert [s.id for s in samples] == ["q1", "q2"]


def test_bad_line_raises_with_line_number(tmp_path):
    """坏数据落在第 3 行（中间垫了个空行），报错里必须说"第 3 行"。

    而不是"第 2 条"。这个区别能挡住"用样本计数器冒充行号"的错误实现。
    """
    path = tmp_path / "bad.jsonl"
    path.write_text(
        '{"id": "q1", "prompt": "第一条没问题"}\n\n{"id": "q2"}\n',
        encoding="utf-8",
    )

    with pytest.raises(SampleFormatError, match="第 3 行"):
        load_samples(path)


def test_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_samples(tmp_path / "not-here.jsonl")
