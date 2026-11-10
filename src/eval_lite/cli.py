"""命令行入口。

`pyproject.toml` 里写着 `eval-lite = "eval_lite.cli:main"`，
所以这个模块必须有 `main` 函数 —— 它是命令的落点。

这里就是把前面所有模块接起来的地方。整个项目的「接线图」就在 run() 里。
"""

import asyncio
import logging
from pathlib import Path

import typer

from eval_lite.client import FakeModelClient, HttpModelClient, ModelClient
from eval_lite.config import get_settings
from eval_lite.loader import load_samples
from eval_lite.report import write_reports
from eval_lite.runner import run_all_models

app = typer.Typer(help="批量评测大模型输出，产出可对比的效果报告")

logger = logging.getLogger("eval_lite")


@app.callback()
def _root() -> None:
    """根命令。

    这个 callback 看起来"什么都不做"，但它有个关键作用：

    Typer 在**只有一个命令**时，会把那个命令拍平 —— 直接 `eval-lite --input ...`，
    `run` 这个词根本不需要。加了 callback 之后，它才被当成"一组命令"，
    于是 `eval-lite run --input ...` 才是正确用法。

    为什么要保留 `run` 这个子命令？因为以后会加 `eval-lite compare`、
    `eval-lite init` 之类。现在就定好结构，将来加命令不用改用法。
    """


@app.command()
def run(
    input_path: Path = typer.Option(..., "--input", "-i", help="评测数据（JSONL）"),
    models: str = typer.Option(..., "--models", "-m", help="模型名，逗号分隔"),
    concurrency: int = typer.Option(8, "--concurrency", "-c", help="并发数"),
    output_dir: Path = typer.Option(Path("results"), "--output", "-o", help="输出目录"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="打详细日志"),
) -> None:
    """跑一次评测。

    流水线：
        读配置 → 造客户端 → 读数据 → 并发跑 → 出报告 → 打印结果位置
    """
    settings = get_settings()

    logging.basicConfig(
        level=logging.DEBUG if verbose else settings.log_level,
        format="%(asctime)s %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
        force=True,
    )

    if not input_path.exists():
        raise typer.BadParameter(f"找不到输入文件：{input_path}")

    # ---- 1. 按模型名造客户端 ----
    # "fake" 是特殊的：它不发网络请求，整条流程可以离线跑。
    # 这个分支很重要 —— 它让测试和 CI 都不需要真的调 API。
    names = [m.strip() for m in models.split(",") if m.strip()]
    if not names:
        raise typer.BadParameter("--models 至少要有一个模型名")

    clients: list[ModelClient] = []
    for name in names:
        if name == "fake":
            clients.append(FakeModelClient(name="fake"))
        else:
            clients.append(
                HttpModelClient(
                    base_url=settings.api_base_url,
                    api_key=settings.require_api_key(),
                    name=name,
                )
            )
    logger.info("模型：%s", ", ".join(c.name for c in clients))

    # ---- 2. 读数据 ----
    samples = load_samples(input_path)
    logger.info("读到 %d 条样本（%s）", len(samples), input_path.name)

    # ---- 3. 并发跑 ----
    # asyncio.run 只在这里调一次 —— 它是整个程序的"事件循环入口"。
    # 在 async 函数内部再调 asyncio.run 会报错。
    logger.info("开始评测，并发数 %d ……", concurrency)
    results = asyncio.run(run_all_models(clients, samples, concurrency))

    ok = sum(1 for r in results if r.error is None)
    logger.info("跑完了：成功 %d / 共 %d", ok, len(results))

    # ---- 4. 出报告 ----
    csv_path, md_path = write_reports(results, output_dir)

    typer.echo(f"跑完了：{len(results)} 条结果（成功 {ok} 条）")
    typer.echo(f"  明细：{csv_path}")
    typer.echo(f"  汇总：{md_path}")


def main() -> None:
    """[project.scripts] 指向的就是这里。"""
    app()
