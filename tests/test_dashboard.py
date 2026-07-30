from pathlib import Path

import pytest
from typer.testing import CliRunner

from radar_sustentabilidade import cli, dashboard
from radar_sustentabilidade.cli import app
from radar_sustentabilidade.dashboard import (
    Point,
    _score_columns,
    format_decimal,
    format_integer,
    format_millions,
    format_percent,
    format_ratio,
    line_chart,
    render_dashboard,
    write_dashboard,
)


def sample_data() -> dict:
    points = []
    for year, presencial, ead in (
        (2014, (5_000_000, 2_400_000), (3_000_000, 720_000)),
        (2019, (5_100_000, 2_100_000), (7_000_000, 1_500_000)),
        (2024, (5_070_000, 1_660_000), (18_580_000, 3_350_000)),
    ):
        for modality, (seats, entrants) in enumerate(
            (presencial, ead), start=1
        ):
            points.append(
                Point(
                    year=year,
                    modality=modality,
                    seats=seats,
                    entrants=entrants,
                    occupancy=entrants / seats,
                )
            )
    return {
        "year": 2024,
        "points": points,
        "institutions": [
            {
                "institution_id": 1,
                "institution_name": "Universidade A",
                "institution_state": "SP",
                "unconverted": 4_000_000,
                "occupancy": 0.12,
                "offers": 100,
            },
            {
                "institution_id": 2,
                "institution_name": "Universidade B",
                "institution_state": "PR",
                "unconverted": 2_000_000,
                "occupancy": 0.2,
                "offers": 80,
            },
        ],
        "concentration": [
            {"position": 1, "cumulative_share": 0.216},
            {"position": 10, "cumulative_share": 0.482},
            {"position": 50, "cumulative_share": 0.728},
        ],
        "persistence": [
            {
                "teaching_modality": 1,
                "offers": 24_094,
                "mean_low_share": 0.316,
                "always_idle_share": 0.055,
                "long_streak_share": 0.209,
                "mean_volatility": 0.55,
            },
            {
                "teaching_modality": 2,
                "offers": 1_504,
                "mean_low_share": 0.494,
                "always_idle_share": 0.182,
                "long_streak_share": 0.291,
                "mean_volatility": 0.59,
            },
        ],
        "totals": {
            "institutions": 2_526,
            "unconverted": 18_640_000,
            "seats": 23_650_000,
        },
        "transition": {
            "surviving_pairs": 17_060,
            "substitution_signal_share": 0.123,
            "seat_change_correlation": -0.083,
        },
        "completion": [
            {
                "teaching_modality": 1,
                "eligible_offers": 21_541,
                "coverage_share": 0.619,
                "aggregate_completion_ratio": 0.403,
                "median_offer_ratio": 0.367,
                "exceeds_one_share": 0.039,
            },
            {
                "teaching_modality": 2,
                "eligible_offers": 3_851,
                "coverage_share": 0.342,
                "aggregate_completion_ratio": 0.267,
                "median_offer_ratio": 0.246,
                "exceeds_one_share": 0.062,
            },
        ],
        "alerts": [
            {
                "institution_id": 10,
                "institution_name": "Faculdade de Exemplo",
                "institution_state": "MG",
                "course_id": 100,
                "course_name": "Administração",
                "teaching_modality": 2,
                "enrollments": 1_200,
                "risk": 0.91,
            },
            {
                "institution_id": 11,
                "institution_name": "Instituto de Exemplo",
                "institution_state": "BA",
                "course_id": 200,
                "course_name": "Pedagogia",
                "teaching_modality": 1,
                "enrollments": 800,
                "risk": 0.87,
            },
        ],
    }


def test_formatters_use_brazilian_notation() -> None:
    assert format_millions(18_580_000) == "18,6 M"
    assert format_percent(0.32768) == "32,8%"
    assert format_integer(24_094) == "24.094"
    assert format_ratio(2.918) == "2,9×"
    assert format_decimal(-0.083) == "-0,08"


def test_line_chart_rejects_empty_series() -> None:
    with pytest.raises(ValueError, match="ao menos um ponto"):
        line_chart([], "seats", "Vagas", format_millions)


def test_score_columns_do_not_repeat_modality() -> None:
    columns = _score_columns(["teaching_modality", "enrollments"])

    assert columns.count("teaching_modality") == 1
    assert len(columns) == len(set(columns))


def test_render_dashboard_is_self_contained_and_methodologically_explicit() -> None:
    html = render_dashboard(sample_data())

    assert html.startswith("<!doctype html>")
    assert "<svg" in html
    assert "https://" not in html
    assert "Vagas não convertidas" in html
    assert "Viés de sobrevivência" in html
    assert "operar pelo ranking" in html
    assert "uma oferta por IES" in html
    assert "Sinal de substituição" in html
    assert "Não é taxa de coorte" in html
    assert "Faculdade de Exemplo" in html
    assert 'lang="pt-BR"' in html


def test_write_dashboard_persists_utf8_html(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dashboard, "load_dashboard_data", lambda **_: sample_data())
    monkeypatch.setattr(cli, "write_dashboard", dashboard.write_dashboard)
    output = tmp_path / "dashboard" / "index.html"

    result = write_dashboard(output)

    assert result == output
    assert "Educação Superior" in output.read_text(encoding="utf-8")


def test_build_dashboard_command_uses_requested_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(dashboard, "load_dashboard_data", lambda **_: sample_data())
    output = tmp_path / "painel.html"

    result = CliRunner().invoke(
        app,
        ["build-dashboard", "--output", str(output)],
    )

    assert result.exit_code == 0
    assert output.exists()
    assert "painel em" in result.stdout
