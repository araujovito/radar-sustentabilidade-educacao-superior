"""Relatório reproduzível das métricas analíticas do Marco 3."""

import json
from decimal import Decimal
from pathlib import Path
from typing import Any

NATIONAL_SHARES_QUERY = """
SELECT
    census_year,
    SUM(offered_seats) AS offered_seats,
    SUM(entrants) AS entrants,
    SUM(enrollments) AS enrollments,
    SUM(offered_seats) FILTER (WHERE teaching_modality = 2)::NUMERIC
        / NULLIF(SUM(offered_seats), 0) AS ead_seat_share,
    SUM(entrants) FILTER (WHERE teaching_modality = 2)::NUMERIC
        / NULLIF(SUM(entrants), 0) AS ead_entrant_share,
    SUM(enrollments) FILTER (WHERE teaching_modality = 2)::NUMERIC
        / NULLIF(SUM(enrollments), 0) AS ead_enrollment_share
FROM analytics.course_supply_snapshot
WHERE census_year IN (
    (SELECT MIN(census_year) FROM analytics.course_supply_snapshot),
    (SELECT MIN(census_year) + 5 FROM analytics.course_supply_snapshot),
    (SELECT MAX(census_year) FROM analytics.course_supply_snapshot)
)
GROUP BY census_year
ORDER BY census_year
"""

PORTFOLIO_STATES_QUERY = """
SELECT census_year, modality_state, COUNT(*) AS institution_fields
FROM analytics.modality_portfolio_state
WHERE census_year IN (
    (SELECT MIN(census_year) FROM analytics.course_supply_snapshot),
    (SELECT MAX(census_year) FROM analytics.course_supply_snapshot)
)
GROUP BY census_year, modality_state
ORDER BY census_year, modality_state
"""

LATEST_TRANSITIONS_QUERY = """
SELECT transition, COUNT(*) AS institution_fields
FROM analytics.modality_portfolio_transition
WHERE census_year = (
    SELECT MAX(census_year) FROM analytics.course_supply_snapshot
)
GROUP BY transition
ORDER BY institution_fields DESC, transition
"""

SURVIVING_PANEL_QUERY = """
WITH bounds AS (
    SELECT MIN(census_year) AS first_year, MAX(census_year) AS last_year
    FROM analytics.course_supply_snapshot
),
first_year AS (
    SELECT state.*
    FROM analytics.modality_portfolio_state AS state
    CROSS JOIN bounds
    WHERE state.census_year = bounds.first_year
),
last_year AS (
    SELECT state.*
    FROM analytics.modality_portfolio_state AS state
    CROSS JOIN bounds
    WHERE state.census_year = bounds.last_year
),
paired AS (
    SELECT
        first_year.presencial_seats AS first_presencial_seats,
        last_year.presencial_seats AS last_presencial_seats,
        first_year.ead_seats AS first_ead_seats,
        last_year.ead_seats AS last_ead_seats
    FROM first_year
    JOIN last_year USING (institution_id, cine_label_code)
)
SELECT
    COUNT(*) AS surviving_institution_fields,
    COUNT(*) FILTER (
        WHERE last_ead_seats > first_ead_seats
          AND last_presencial_seats < first_presencial_seats
    ) AS ead_up_presencial_down,
    COUNT(*) FILTER (
        WHERE last_ead_seats > first_ead_seats
          AND last_presencial_seats < first_presencial_seats
    )::NUMERIC / NULLIF(COUNT(*), 0) AS substitution_signal_share,
    CORR(
        last_ead_seats - first_ead_seats,
        last_presencial_seats - first_presencial_seats
    ) AS seat_change_correlation
FROM paired
"""

COMPLETION_QUERY = """
WITH latest AS (
    SELECT MAX(census_year) AS census_year
    FROM analytics.course_supply_snapshot
),
current_offers AS (
    SELECT teaching_modality, COUNT(*) AS offers
    FROM analytics.course_supply_snapshot
    CROSS JOIN latest
    WHERE course_supply_snapshot.census_year = latest.census_year
      AND graduates IS NOT NULL
    GROUP BY teaching_modality
)
SELECT
    summary.census_year,
    summary.teaching_modality,
    summary.lag_years,
    summary.eligible_offers,
    current_offers.offers AS current_offers,
    summary.eligible_offers::NUMERIC
        / NULLIF(current_offers.offers, 0) AS coverage_share,
    summary.aggregate_completion_ratio,
    summary.median_offer_ratio,
    summary.exceeds_one_share
FROM analytics.lagged_completion_summary AS summary
JOIN current_offers USING (teaching_modality)
CROSS JOIN latest
WHERE summary.census_year = latest.census_year
ORDER BY teaching_modality, lag_years
"""

AREA_DEPENDENCY_QUERY = """
SELECT
    cine_label_code,
    cine_label_name,
    COALESCE(presencial_seats, 0) + COALESCE(ead_seats, 0)
        AS offered_seats,
    ead_seat_share,
    ead_entrant_share,
    ead_seat_share - ead_entrant_share AS conversion_gap
FROM analytics.modality_dependency
WHERE census_year = (
    SELECT MAX(census_year) FROM analytics.course_supply_snapshot
)
ORDER BY offered_seats DESC
LIMIT 15
"""


def _plain(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _query(connection, sql: str) -> list[dict]:
    from sqlalchemy import text

    return [
        {key: _plain(value) for key, value in row.items()}
        for row in connection.execute(text(sql)).mappings()
    ]


def load_milestone3_data() -> dict:
    """Consulta as métricas do Marco 3 no PostgreSQL."""
    from sqlalchemy import create_engine

    from radar_sustentabilidade.config import Settings

    engine = create_engine(Settings().database_url)
    try:
        with engine.connect() as connection:
            return {
                "national_modality_shares": _query(
                    connection, NATIONAL_SHARES_QUERY
                ),
                "portfolio_states": _query(connection, PORTFOLIO_STATES_QUERY),
                "latest_transitions": _query(
                    connection, LATEST_TRANSITIONS_QUERY
                ),
                "surviving_panel": _query(
                    connection, SURVIVING_PANEL_QUERY
                )[0],
                "lagged_completion": _query(connection, COMPLETION_QUERY),
                "largest_fields": _query(connection, AREA_DEPENDENCY_QUERY),
            }
    finally:
        engine.dispose()


def build_milestone3_report(data: dict) -> dict:
    """Acrescenta definições e ressalvas às métricas consultadas."""
    years = [
        int(row["census_year"])
        for row in data["national_modality_shares"]
    ]
    return {
        "schema_version": 1,
        "period": {"first_year": min(years), "last_year": max(years)},
        "unit_of_analysis": {
            "modality_transition": "instituição × área CINE × ano",
            "lagged_completion": "oferta × ano × defasagem",
        },
        "definitions": {
            "substitution_signal": (
                "EAD cresce e presencial recua na mesma IES e área CINE "
                "entre o primeiro e o último ano, entre pares sobreviventes"
            ),
            "lagged_completion_ratio": (
                "concluintes no ano t divididos por ingressantes da mesma "
                "oferta em t-3, t-4 ou t-5"
            ),
            "completion_eligibility": (
                "ao menos 20 ingressantes no ano-base e presença da oferta "
                "nos dois anos comparados"
            ),
        },
        "limitations": [
            "O sinal de substituição é descritivo e não identifica causalidade.",
            (
                "A proxy de conclusão não rastreia indivíduos, transferências "
                "nem duração específica de cada curso."
            ),
            (
                "Resultados de conclusão acima de 100% são preservados como "
                "diagnóstico de mistura de coortes, não truncados."
            ),
        ],
        "metrics": data,
    }


def write_milestone3_report(
    output_path: Path = Path("reports/milestone3/metrics.json"),
) -> Path:
    """Gera e persiste o relatório do Marco 3."""
    report = build_milestone3_report(load_milestone3_data())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path
