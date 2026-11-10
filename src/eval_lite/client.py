"""调模型。

接口约定（第 5 天学的 Protocol）：
    任何有 `name` 属性和 `async complete(prompt) -> str` 方法的东西，
    都算一个「模型客户端」。

上层代码只依赖这个形状，不认识具体是 HTTP 还是假的 ——
这就是为什么整条流程能在离线状态下被测试、能在 CI 上跑。
"""

import asyncio
from typing import Protocol

import httpx


class ModelClient(Protocol):
    name: str

    async def complete(self, prompt: str) -> str: ...


class HttpModelClient:
    """真实实现：发 HTTP 请求。

    用 httpx.AsyncClient —— 注意是异步版本。用同步的 requests 会把整个
    事件循环卡住，并发就完全失效了（第 13 天那个坑）。

    这里的请求/响应格式是**示意**的：真实的模型 API 各有各的协议，
    你接的时候只改这一个类就行，上层代码一个字都不用动 ——
    这正是把外部细节关在一个文件里的价值。
    """

    def __init__(
        self,
        base_url: str,
        api_key: str,
        name: str,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.name = name
        self.timeout = timeout

    async def complete(self, prompt: str) -> str:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"prompt": prompt},
            )
            # raise_for_status 会把 4xx/5xx 变成异常 —— 让 runner 那边统一处理，
            # 不要在这里吞掉，否则报告里会显示"成功但答案是空的"。
            resp.raise_for_status()
            data = resp.json()

        if not isinstance(data, dict) or "answer" not in data:
            raise ValueError(f"响应里没有 answer 字段：{data!r}")
        return str(data["answer"])


class FakeModelClient:
    """离线用的假客户端。

    它的存在让你能在不联网、不花钱的情况下，把整条流程从头跑到尾 ——
    包括测试、包括 CI。这是第 10 天的核心思路。

    返回的格式故意和真客户端对齐：都是"一个答案字符串"。
    这样上层完全看不出区别。
    """

    def __init__(self, name: str = "fake", latency: float = 0.05) -> None:
        self.name = name
        self.latency = latency

    async def complete(self, prompt: str) -> str:
        # 注意是 await asyncio.sleep，不是 time.sleep。
        # 后者会把事件循环卡死，"并发"变成"排队"。
        await asyncio.sleep(self.latency)
        return f"回答：{prompt}"
