from click.testing import CliRunner


def test_version():
    """
    CLI test: Invoke `pueblo --version`
    """
    from pueblo.cli import cli

    runner = CliRunner()

    result = runner.invoke(
        cli,
        args="--version",
        catch_exceptions=False,
    )
    assert result.exit_code == 0
