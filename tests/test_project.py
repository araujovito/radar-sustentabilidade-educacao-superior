from typer.testing import CliRunner

from radar_sustentabilidade import __version__
from radar_sustentabilidade.cli import app
from radar_sustentabilidade.config import Settings

runner = CliRunner()


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_default_database_settings() -> None:
    settings = Settings()

    assert settings.postgres_db == "radar_educacao"
    assert settings.postgres_port == 5432


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == __version__


def test_inventory_command_help() -> None:
    result = runner.invoke(app, ["inventory", "--help"])

    assert result.exit_code == 0
    assert "Valida um ZIP" in result.stdout
