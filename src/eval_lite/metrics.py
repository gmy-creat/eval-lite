"""判分。

全是纯函数：没有网络、没有文件、没有全局状态 —— 最好测的那类代码。
"""

import re

# 结尾的标点，中英文都算
_TRAILING_PUNCT = re.compile(r"[。，！？、；：.,!?;:]+$")
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """归一化答案，方便比较。

    四步：去首尾空白 → 转小写 → 压缩连续空白 → 去结尾标点 → 再 strip 一次。

    最后那个 strip 不能省：删掉标点之后可能留下尾随空格，
    例如 "Paris . " 删完标点会变成 "paris "，不 strip 就比不过 "paris"。
    """
    text = text.strip().lower()
    text = _WHITESPACE.sub(" ", text)
    text = _TRAILING_PUNCT.sub("", text)
    return text.strip()


def exact_match(prediction: str, reference: str) -> bool:
    """归一化之后完全相同，算命中。"""
    return normalize(prediction) == normalize(reference)


def contains_match(prediction: str, reference: str) -> bool:
    """参考答案出现在预测结果里，算命中。比 exact_match 宽松。

    注意它对短答案很不友好："1" 会匹配进 "10000" 里。
    数字、日期这类短答案应该只用 exact_match。
    """
    return normalize(reference) in normalize(prediction)


def accuracy(results: list[bool]) -> float:
    """算准确率。

    空列表直接抛错，而不是返回 0.0 —— 返回 0.0 会让
    "一条都没跑出来"和"全错了"变成同一个数字，以后你分不清
    是模型不行还是任务挂了。
    """
    if not results:
        raise ValueError("结果列表为空，无法计算准确率")
    return sum(results) / len(results)
