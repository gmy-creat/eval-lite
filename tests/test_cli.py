"""命令行那层。这层很薄，验到"能用"就行。"""

from typer.testing import CliRunner

from eval_lite.cli import app


def test_help_works():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_run_command_lists_its_options():
    runner = CliRunner()
    result = runner.invoke(app, ["run", "--help"])

    assert result.exit_code == 0
    for opt in ("--input", "--models", "--concurrency", "--output", "--verbose"):
        assert opt in result.output


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
