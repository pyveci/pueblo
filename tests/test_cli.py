from click.testing import CliRunner

from pueblo.cli import cli


def test_version():
    """
    CLI test: Invoke `pueblo --version`
    """
    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--version",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
