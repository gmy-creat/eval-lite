"""并发调度 —— 把样本发给模型，收集结果。

三个要点（都来自第 13 天）：
  1. gather 并发，Semaphore 限流
  2. 单条失败不影响整批 —— 失败记成 Result(error=...)，不往上抛
  3. 每条都记 latency_ms，报告里要用
"""

import asyncio
import time

from eval_lite.client import ModelClient
from eval_lite.metrics import exact_match
from eval_lite.models import Result, Sample


async def run_model(
    client: ModelClient,
    samples: list[Sample],
    concurrency: int = 8,
) -> list[Result]:
    """用一个客户端跑完所有样本。

    结果顺序和输入一一对应（gather 是保序的），
    所以 report 那边可以靠下标把结果和样本对上。
    """
    if concurrency < 1:
        raise ValueError("concurrency 至少是 1")

    sem = asyncio.Semaphore(concurrency)

    async def one(sample: Sample) -> Result:
        # 计时放在 sem 里面：这样 latency 只算"请求本身花了多久"，
        # 不含排队等并发名额的时间。想拿"用户实际等了多久"，
        # 那是另一回事（可以在 CLI 那边计整轮总耗时）。
        async with sem:
            start = time.perf_counter()
            try:
                answer = await client.complete(sample.prompt)
            except Exception as e:
                return Result(
                    sample_id=sample.id,
                    model=client.name,
                    latency_ms=(time.perf_counter() - start) * 1000,
                    error=f"{type(e).__name__}: {e}",
                )

            return Result(
                sample_id=sample.id,
                model=client.name,
                answer=answer,
                correct=exact_match(answer, sample.reference),
                latency_ms=(time.perf_counter() - start) * 1000,
            )

    return await asyncio.gather(*[one(s) for s in samples])


async def run_all_models(
    clients: list[ModelClient],
    samples: list[Sample],
    concurrency: int = 8,
) -> list[Result]:
    """跑多个模型，结果拼成一个扁平的列表。

    **这里选了「模型之间串行、模型内部并发」。**

    另一种做法是模型之间也并发，但那会让总并发数变成
    「模型数 × concurrency」—— 你设了 8，实际发出去 24 个请求。
    对 API 的速率限制来说，这个差别是致命的。

    串行跑模型还有个好处：日志和进度更清楚，一个一个来，
    出问题也好定位是哪个模型。
    """
    results: list[Result] = []
    for client in clients:
        results.extend(await run_model(client, samples, concurrency))
    return results
