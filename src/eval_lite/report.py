"""出报告。

两份输出，各有各的读者：
  - CSV：给机器和表格软件看的，一条样本一行，方便你继续分析
  - Markdown：给人看的，每个模型一行，横向对比

**统计口径（这个决定很重要，报告里也写明了）**：
失败的样本（error 不为空）**不计入准确率**，单独用「失败」列统计。

为什么这么选？因为"请求超时"和"答错了"是两件完全不同的事。
混在一起算，会让网络抖动看起来像模型变笨了。分开报，
读的人才知道该去优化模型还是该去修网络。

另一种常见做法是"失败算答错"，那更保守，但必须写清楚 ——
不写清楚的话，两个报告数字根本没法互相比较。
"""

import csv
import io
from pathlib import Path

from eval_lite.models import Result


def to_csv(results: list[Result]) -> str:
    """每条样本一行：sample_id, model, answer, correct, latency_ms, error。"""
    buf = io.StringIO()
    # 显式指定 \n 结尾。默认是 \r\n，而 write_text 在 Windows 上会把 \n 再转成
    # \r\n，最后文件里变成 \r\r\n —— 用 Excel 打开每行之间会多一个空行。
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(["sample_id", "model", "answer", "correct", "latency_ms", "error"])

    for r in results:
        writer.writerow(
            [
                r.sample_id,
                r.model,
                r.answer or "",
                "" if r.correct is None else str(r.correct),
                f"{r.latency_ms:.1f}",
                r.error or "",
            ]
        )

    return buf.getvalue()


def to_markdown(results: list[Result]) -> str:
    """汇总报告：每个模型一行，横向对比。"""
    by_model: dict[str, list[Result]] = {}
    for r in results:
        by_model.setdefault(r.model, []).append(r)

    lines = ["# 评测报告", ""]
    lines.append(f"总结果数：{len(results)}")
    lines.append("")
    lines.append(
        "> **统计口径**：失败（error 不为空）的样本不计入准确率，"
        "单独在「失败」列统计；准确率 = 答对条数 / 成功返回条数。"
    )
    lines.append("")
    lines.append("| 模型 | 样本数 | 成功 | 失败 | 准确率 | 平均延迟 (ms) |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")

    for model, rs in by_model.items():
        ok = [r for r in rs if r.error is None]
        n_fail = len(rs) - len(ok)
        correct = [r.correct for r in ok if r.correct is not None]

        acc = f"{sum(correct) / len(correct):.1%}" if correct else "—"
        avg_latency = f"{sum(r.latency_ms for r in ok) / len(ok):.1f}" if ok else "—"

        lines.append(f"| {model} | {len(rs)} | {len(ok)} | {n_fail} | {acc} | {avg_latency} |")

    lines.append("")
    return "\n".join(lines)


def write_reports(results: list[Result], output_dir: Path) -> tuple[Path, Path]:
    """把两份报告写进 output_dir，返回 (csv 路径, markdown 路径)。"""
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / "results.csv"
    md_path = output_dir / "report.md"

    # CSV 用 utf-8-sig（带 BOM）：这样用 Excel 双击打开时中文不会乱码。
    # 普通 utf-8 在 Excel 里会被当成 GBK 解读，中文全变成问号。
    csv_path.write_text(to_csv(results), encoding="utf-8-sig")
    md_path.write_text(to_markdown(results), encoding="utf-8")

    return csv_path, md_path
