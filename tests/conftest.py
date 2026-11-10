"""多个测试文件共用的 fixture。

pytest 会自动加载这个文件，同目录和所有子目录下的测试都能直接用，不用 import。
"""

import pytest

from eval_lite.client import FakeModelClient


@pytest.fixture
def fake_client() -> FakeModelClient:
    """离线假客户端。

    latency 设成 0.01：够小不拖慢测试，又足以让并发"同时在场的瞬间"被抓到。
    """
    return FakeModelClient(name="fake", latency=0.01)


@pytest.fixture
def sample_qa_file(tmp_path):
    """一个内容已知的临时数据文件。

    故意自己造，而不是用 data/qa.jsonl —— 改动真实数据文件不该让测试挂。
    """
    path = tmp_path / "qa.jsonl"
    path.write_text(
        '{"id": "q1", "prompt": "法国的首都是哪里？", "reference": "巴黎"}\n'
        '{"id": "q2", "prompt": "1 + 1 等于几？", "reference": "2"}\n'
        '{"id": "q3", "prompt": "水的化学式是什么？", "reference": "H2O"}\n',
        encoding="utf-8",
    )
    return path
