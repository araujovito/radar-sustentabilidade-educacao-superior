import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from radar_sustentabilidade import cli, milestone3
from radar_sustentabilidade.cli import app
from radar_sustentabilidade.milestone3 import (
    build_milestone3_report,
    write_milestone3_report,
)


def sample_data() -> dict:
    return {
        "national_modality_shares": [
            {
                "census_year": 2014,
                "offered_seats": 100,
                "entrants": 50,
                "enrollments": 200,
                "ead_seat_share": 0.2,
                "ead_entrant_share": 0.1,
                "ead_enrollment_share": 0.08,
            },
            {
                "census_year": 2024,
                "offered_seats": 300,
                "entrants": 80,
                "enrollments": 260,
                "ead_seat_share": 0.75,
                "ead_entrant_share": 0.65,
                "ead_enrollment_share": 0.5,
            },
        ],
        "portfolio_states": [],
        "latest_transitions": [],
        "surviving_panel": {
            "surviving_institution_fields": 100,
            "ead_up_presencial_down": 12,
            "substitution_signal_share": 0.12,
            "seat_change_correlation": -0.08,
        },
        "lagged_completion": [],
        "largest_fields": [],
    }


def test_report_documents_units_definitions_and_limitations() -> None:
    report = build_milestone3_report(sample_data())

    assert report["period"] == {"first_year": 2014, "last_year": 2024}
    assert "área CINE" in report["unit_of_analysis"]["modality_transition"]
    assert "t-3" in report["definitions"]["lagged_completion_ratio"]
    assert len(report["limitations"]) == 3


def test_write_report_persists_utf8_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        milestone3, "load_milestone3_data", sample_data
    )
    output = tmp_path / "metrics.json"

    result = write_milestone3_report(output)
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert result == output
    assert saved["schema_version"] == 1
    assert saved["period"]["last_year"] == 2024


def test_cli_builds_milestone3_report(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        milestone3, "load_milestone3_data", sample_data
    )
    monkeypatch.setattr(
        cli, "write_milestone3_report", milestone3.write_milestone3_report
    )
    output = tmp_path / "metrics.json"

    result = CliRunner().invoke(
        app,
        ["build-milestone3-report", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "relatório em" in result.stdout
