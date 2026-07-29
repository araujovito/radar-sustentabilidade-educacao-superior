from radar_sustentabilidade import __version__
from radar_sustentabilidade.config import Settings


def test_version_is_defined() -> None:
    assert __version__ == "0.1.0"


def test_default_database_settings() -> None:
    settings = Settings()

    assert settings.postgres_db == "radar_educacao"
    assert settings.postgres_port == 5432
