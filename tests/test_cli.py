"""命令行那层。

原则：**测行为，不测渲染出来的文字。**

之前这里有个测试是断言 `"--input" in result.output` —— 在 Windows 上跑得好好的，
到了 Linux CI 上就挂了。原因是 Typer 底下的 Rich 会把帮助文本渲染成带颜色、
带换行的富文本，终端宽度、颜色支持、rich 版本都会改变它的样子。

断言渲染结果，测的是"界面长什么样"；而界面本来就会变。
所以下面改成：直接把这些选项**用一遍**，看它是不是真的能用。
"""

from typer.testing import CliRunner

from eval_lite.cli import app


def test_help_works():
    runner = CliRunner()

    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0


def test_run_subcommand_exists():
    runner = CliRunner()

    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0


def test_run_end_to_end_with_fake_model(tmp_path, sample_qa_file):
    """端到端：用假客户端跑一遍，两个报告文件都要生成。"""
    runner = CliRunner()
    out = tmp_path / "out"

    result = runner.invoke(
        app,
        ["run", "-i", str(sample_qa_file), "-m", "fake", "-o", str(out)],
    )

    assert result.exit_code == 0, result.output
    assert (out / "results.csv").exists()
    assert (out / "report.md").exists()


def test_run_accepts_all_options(tmp_path, sample_qa_file):
    """所有长选项都真的能用 —— 这是"测行为"替代"测帮助文本"。"""
    runner = CliRunner()
    out = tmp_path / "out"

    result = runner.invoke(
        app,
        [
            "run",
            "--input",
            str(sample_qa_file),
            "--models",
            "fake",
            "--concurrency",
            "2",
            "--output",
            str(out),
        ],
    )

    assert result.exit_code == 0, result.output
    assert (out / "report.md").exists()
