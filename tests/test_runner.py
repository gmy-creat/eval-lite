"""runner 的测试 —— 这是最值钱的几个。"""

import asyncio

from eval_lite.loader import load_samples
from eval_lite.runner import run_model


async def test_returns_result_per_sample(fake_client, sample_qa_file):
    samples = load_samples(sample_qa_file)

    results = await run_model(fake_client, samples, concurrency=3)

    assert len(results) == len(samples)
    assert [r.sample_id for r in results] == [s.id for s in samples]
    assert all(r.error is None for r in results)


async def test_failure_does_not_break_the_batch(sample_qa_file):
    """单条失败：那条记成 error，其余照常返回。"""

    class FlakyClient:
        name = "flaky"

        def __init__(self) -> None:
            self.calls = 0

        async def complete(self, prompt: str) -> str:
            self.calls += 1
            if self.calls == 2:
                raise ConnectionError("模拟第二次调用失败")
            return f"回答：{prompt}"

    samples = load_samples(sample_qa_file)

    # concurrency=1 保证调用顺序确定，第 2 次才会失败
    results = await run_model(FlakyClient(), samples, concurrency=1)

    assert len(results) == len(samples)
    errors = [r for r in results if r.error is not None]
    assert len(errors) == 1
    assert "ConnectionError" in (errors[0].error or "")


async def test_concurrency_limit_is_respected(fake_client, sample_qa_file, monkeypatch):
    """限流有没有生效 —— 数"同时在场"的峰值。

    光看返回值验不出限流：并发 3 和并发 20 返回的内容一模一样。
    所以要换一个"间谍"函数，记录执行期间的最大同时在跑数。
    """
    running = 0
    peak = 0

    async def spy(prompt: str) -> str:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        return f"回答：{prompt}"

    monkeypatch.setattr(fake_client, "complete", spy)

    samples = load_samples(sample_qa_file) * 5  # 15 条
    await run_model(fake_client, samples, concurrency=3)

    assert peak <= 3
