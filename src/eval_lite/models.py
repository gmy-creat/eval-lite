"""贯穿全流程的两个数据模型。

这两个是整个项目的「接口约定」—— 所有模块之间传的都是它们。
所以先把它们定死，后面每个模块才能独立地写、独立地测。
"""

from pydantic import BaseModel, Field


class Sample(BaseModel):
    """一条评测样本。"""

    id: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    reference: str = ""


class Result(BaseModel):
    """一次模型调用的结果。

    成功时：answer 和 correct 有值，error 是 None。
    失败时：error 有值，answer 和 correct 是 None。

    这个「二选一」的约定很重要 —— 它让后面 report 那边好写很多：
    看到 error 就知道这条废了，不用去猜。
    """

    sample_id: str
    model: str
    answer: str | None = None
    correct: bool | None = None
    latency_ms: float = 0.0
    error: str | None = None
