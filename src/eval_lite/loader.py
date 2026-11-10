"""读 JSONL 评测数据。

每行一个样本；空行跳过；坏数据抛 SampleFormatError，报错里带文件行号。

和单独脚本版的唯一区别：`Sample` 不再在本文件里定义，而是从 models 导入 ——
全项目只保留一份模型定义，不会出现两个"长得一样但不是同一个类"的 Sample。
"""

import json
from pathlib import Path

from pydantic import ValidationError

from eval_lite.models import Sample


class SampleFormatError(ValueError):
    """某一行的数据不符合样本格式。"""


def load_samples(path: Path) -> list[Sample]:
    """读取 JSONL 文件，每行一个样本。

    行号用 enumerate 的真实文件行号，不是"第几条有效样本"——
    空行虽然被跳过，但它仍然占一行。这个区别有测试专门盯着。
    """
    samples: list[Sample] = []

    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                raw = json.loads(line)
            except json.JSONDecodeError as e:
                raise SampleFormatError(f"{path.name} 第 {lineno} 行不是合法 JSON：{e.msg}") from e

            try:
                samples.append(Sample.model_validate(raw))
            except ValidationError as e:
                first = e.errors()[0]
                field = ".".join(str(p) for p in first["loc"]) or "(根)"
                raise SampleFormatError(
                    f"{path.name} 第 {lineno} 行校验失败：字段 {field} —— {first['msg']}"
                ) from e

    return samples
