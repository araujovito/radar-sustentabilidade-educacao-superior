"""Painel de decisão em HTML autocontido.

O painel é gerado, não editado à mão, e não faz nenhuma requisição externa:
todo o CSS, o SVG e os dados ficam embutidos no arquivo. Isso permite abri-lo
localmente, versioná-lo e publicá-lo sem servidor.

As cores vêm dos dois primeiros slots da paleta categórica de referência, sem
modificação: azul para presencial e laranja para EAD. Duas séries dispensam
qualquer geração de cor.
"""

from dataclasses import dataclass
from html import escape
from pathlib import Path

# Slots 1 e 2 da paleta de referência, com os passos próprios de cada modo.
SERIES_LIGHT = {1: "#2a78d6", 2: "#eb6834"}
SERIES_DARK = {1: "#3987e5", 2: "#d95926"}
MODALITY_LABELS = {1: "Presencial", 2: "EAD"}


@dataclass(frozen=True)
class Point:
    """Observação anual de uma modalidade."""

    year: int
    modality: int
    seats: int
    entrants: int
    occupancy: float


def format_millions(value: float) -> str:
    """Formata um total grande em milhões, no padrão brasileiro."""
    return f"{value / 1_000_000:.1f}".replace(".", ",") + " M"


def format_percent(value: float, decimals: int = 1) -> str:
    """Formata uma proporção como porcentagem no padrão brasileiro."""
    return f"{value * 100:.{decimals}f}".replace(".", ",") + "%"


def format_integer(value: int) -> str:
    """Formata um inteiro com ponto como separador de milhar."""
    return f"{value:,}".replace(",", ".")


def format_ratio(value: float) -> str:
    """Formata um multiplicador com vírgula decimal."""
    return f"{value:.1f}".replace(".", ",") + "×"


def format_decimal(value: float, decimals: int = 2) -> str:
    """Formata um decimal sem unidade no padrão brasileiro."""
    return f"{value:.{decimals}f}".replace(".", ",")


def _scale(value: float, lower: float, upper: float, size: float) -> float:
    if upper == lower:
        return size / 2
    return (value - lower) / (upper - lower) * size


def line_chart(
    points: list[Point],
    measure: str,
    title: str,
    y_formatter,
    y_max: float | None = None,
) -> str:
    """Desenha uma série temporal por modalidade.

    Um eixo apenas. As duas séries recebem rótulo direto no fim da linha, de
    modo que a identidade nunca depende só da cor.
    """
    if not points:
        raise ValueError("O gráfico de linha exige ao menos um ponto")

    width, height = 720, 300
    left, right, top, bottom = 62, 96, 28, 40
    plot_width = width - left - right
    plot_height = height - top - bottom

    years = sorted({point.year for point in points})
    values = [getattr(point, measure) for point in points]
    upper = y_max if y_max is not None else max(values) * 1.08
    lower = 0.0

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="{escape(title)}" class="chart">'
    ]

    # Grade recessiva com quatro divisões.
    for index in range(5):
        ratio = index / 4
        y = top + plot_height - ratio * plot_height
        label = y_formatter(lower + ratio * (upper - lower))
        parts.append(
            f'<line class="grid" x1="{left}" y1="{y:.1f}" '
            f'x2="{left + plot_width}" y2="{y:.1f}"/>'
        )
        parts.append(
            f'<text class="axis" x="{left - 10}" y="{y + 4:.1f}" '
            f'text-anchor="end">{escape(label)}</text>'
        )

    for year in years:
        x = left + _scale(year, years[0], years[-1], plot_width)
        if year in (years[0], years[len(years) // 2], years[-1]):
            parts.append(
                f'<text class="axis" x="{x:.1f}" '
                f'y="{top + plot_height + 22}" '
                f'text-anchor="middle">{year}</text>'
            )

    for modality in (1, 2):
        series = sorted(
            (point for point in points if point.modality == modality),
            key=lambda point: point.year,
        )
        if not series:
            continue
        coordinates = [
            (
                left + _scale(point.year, years[0], years[-1], plot_width),
                top + plot_height
                - _scale(getattr(point, measure), lower, upper, plot_height),
            )
            for point in series
        ]
        path = " ".join(
            f"{'M' if index == 0 else 'L'}{x:.1f},{y:.1f}"
            for index, (x, y) in enumerate(coordinates)
        )
        parts.append(
            f'<path d="{path}" fill="none" class="line series-{modality}"/>'
        )
        for (x, y), point in zip(coordinates, series, strict=True):
            value = y_formatter(getattr(point, measure))
            parts.append(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="9" '
                f'class="hit series-{modality}">'
                f"<title>{point.year} · {MODALITY_LABELS[modality]} · "
                f"{escape(value)}</title></circle>"
            )
        last_x, last_y = coordinates[-1]
        parts.append(
            f'<text class="direct-label series-{modality}" '
            f'x="{last_x + 12:.1f}" y="{last_y + 4:.1f}">'
            f"{MODALITY_LABELS[modality]}</text>"
        )

    parts.append("</svg>")
    return "".join(parts)


def ranked_bars(rows: list[dict], value_key: str, label_key: str) -> str:
    """Desenha barras horizontais ordenadas por magnitude.

    A ordenação carrega o significado, então a cor é um único tom sequencial:
    nenhuma identidade categórica está em jogo.
    """
    if not rows:
        raise ValueError("O gráfico de barras exige ao menos uma linha")

    row_height, gap = 26, 6
    width = 720
    label_width = 268
    bar_area = width - label_width - 96
    height = len(rows) * (row_height + gap) + 16

    maximum = max(row[value_key] for row in rows)
    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Instituições por vagas não convertidas" class="chart">'
    ]

    for index, row in enumerate(rows):
        y = index * (row_height + gap) + 8
        bar_width = max(_scale(row[value_key], 0, maximum, bar_area), 2)
        parts.append(
            f'<text class="row-label" x="0" y="{y + row_height * 0.68:.1f}">'
            f"{escape(str(row[label_key])[:38])}</text>"
        )
        parts.append(
            f'<rect x="{label_width}" y="{y}" width="{bar_width:.1f}" '
            f'height="{row_height}" rx="4" class="bar">'
            f"<title>{escape(str(row[label_key]))} · "
            f"{format_integer(int(row[value_key]))} vagas não convertidas</title>"
            f"</rect>"
        )
        parts.append(
            f'<text class="bar-value" '
            f'x="{label_width + bar_width + 10:.1f}" '
            f'y="{y + row_height * 0.68:.1f}">'
            f"{format_millions(row[value_key])}</text>"
        )

    parts.append("</svg>")
    return "".join(parts)


def paired_bars(rows: list[dict]) -> str:
    """Compara presencial e EAD em cada medida de persistência."""
    if not rows:
        raise ValueError("O gráfico comparativo exige ao menos uma linha")

    width = 720
    group_height = 62
    label_width = 250
    bar_area = width - label_width - 90
    height = len(rows) * group_height + 12

    parts = [
        f'<svg viewBox="0 0 {width} {height}" role="img" '
        f'aria-label="Persistência por modalidade" class="chart">'
    ]

    for index, row in enumerate(rows):
        base = index * group_height + 10
        parts.append(
            f'<text class="row-label" x="0" y="{base + 20}">'
            f"{escape(row['label'])}</text>"
        )
        for offset, modality in enumerate((1, 2)):
            value = row[modality]
            y = base + offset * 22
            bar_width = max(_scale(value, 0, row["maximum"], bar_area), 2)
            parts.append(
                f'<rect x="{label_width}" y="{y}" '
                f'width="{bar_width:.1f}" height="18" rx="4" '
                f'class="bar series-{modality}">'
                f"<title>{escape(row['label'])} · "
                f"{MODALITY_LABELS[modality]} · {escape(row['fmt'](value))}"
                f"</title></rect>"
            )
            parts.append(
                f'<text class="bar-value" '
                f'x="{label_width + bar_width + 10:.1f}" y="{y + 13}">'
                f"{escape(row['fmt'](value))}</text>"
            )

    parts.append("</svg>")
    return "".join(parts)


def stat_tile(value: str, label: str, note: str) -> str:
    """Número de destaque com sua leitura."""
    return (
        '<div class="tile">'
        f'<div class="tile-value">{escape(value)}</div>'
        f'<div class="tile-label">{escape(label)}</div>'
        f'<div class="tile-note">{escape(note)}</div>'
        "</div>"
    )


STYLE = """
:root {
  color-scheme: light dark;
  --surface: #fcfcfb;
  --surface-raised: #ffffff;
  --border: #e3e2dd;
  --text-primary: #0b0b0b;
  --text-secondary: #52514e;
  --text-muted: #78776f;
  --grid: #ebeae5;
  --bar: #2a78d6;
  --series-1: #2a78d6;
  --series-2: #eb6834;
  --critical: #d03b3b;
}
@media (prefers-color-scheme: dark) {
  :root:where(:not([data-theme="light"])) {
    --surface: #1a1a19;
    --surface-raised: #232322;
    --border: #383835;
    --text-primary: #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted: #9d9c92;
    --grid: #2e2e2c;
    --bar: #3987e5;
    --series-1: #3987e5;
    --series-2: #d95926;
    --critical: #d03b3b;
  }
}
:root[data-theme="dark"] {
  --surface: #1a1a19;
  --surface-raised: #232322;
  --border: #383835;
  --text-primary: #ffffff;
  --text-secondary: #c3c2b7;
  --text-muted: #9d9c92;
  --grid: #2e2e2c;
  --bar: #3987e5;
  --series-1: #3987e5;
  --series-2: #d95926;
  --critical: #d03b3b;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 32px 20px 64px;
  background: var(--surface);
  color: var(--text-primary);
  font: 16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        Helvetica, Arial, sans-serif;
}
.wrap { max-width: 980px; margin: 0 auto; }
.masthead {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 28px;
}
.eyebrow {
  margin: 0 0 8px;
  color: var(--series-1);
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
h1 { font-size: 1.85rem; line-height: 1.18; margin: 0 0 8px; }
h2 {
  font-size: 1.18rem;
  margin: 40px 0 4px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}
.subtitle { color: var(--text-secondary); margin: 0; max-width: 720px; }
.lede { color: var(--text-secondary); margin: 0 0 18px; font-size: 0.95rem; }
.theme-toggle {
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface-raised);
  color: var(--text-secondary);
  cursor: pointer;
  font: inherit;
  font-size: 0.8rem;
  padding: 7px 12px;
  white-space: nowrap;
}
.theme-toggle:hover { color: var(--text-primary); }
.section-kicker {
  color: var(--text-muted);
  font-size: 0.8rem;
  margin: 0 0 3px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin: 24px 0 8px;
}
.tile {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
}
.tile-value { font-size: 1.7rem; font-weight: 600; letter-spacing: -0.02em; }
.tile-label { font-size: 0.9rem; color: var(--text-secondary); margin-top: 2px; }
.tile-note { font-size: 0.8rem; color: var(--text-muted); margin-top: 6px; }
.split {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(250px, 0.75fr);
  gap: 24px;
  align-items: start;
}
.split > * { min-width: 0; }
.insight {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px 18px;
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-top: 58px;
}
.insight strong { color: var(--text-primary); }
.insight p:first-child { margin-top: 0; }
.insight p:last-child { margin-bottom: 0; }
.panel { overflow-x: auto; margin-top: 14px; }
.chart { width: 100%; height: auto; min-width: 560px; display: block; }
.grid { stroke: var(--grid); stroke-width: 1; }
.axis { fill: var(--text-muted); font-size: 11px; }
.line { stroke-width: 2; stroke-linejoin: round; stroke-linecap: round; }
.line.series-1 { stroke: var(--series-1); }
.line.series-2 { stroke: var(--series-2); }
.hit { fill: transparent; stroke: none; }
.hit:hover { fill: currentColor; fill-opacity: 0.18; }
.hit.series-1 { color: var(--series-1); }
.hit.series-2 { color: var(--series-2); }
.direct-label { font-size: 11.5px; font-weight: 600; }
.direct-label.series-1 { fill: var(--series-1); }
.direct-label.series-2 { fill: var(--series-2); }
.row-label { fill: var(--text-secondary); font-size: 12px; }
.bar { fill: var(--bar); }
.bar.series-1 { fill: var(--series-1); }
.bar.series-2 { fill: var(--series-2); }
.bar-value { fill: var(--text-secondary); font-size: 11.5px; }
.legend {
  display: flex;
  gap: 18px;
  flex-wrap: wrap;
  margin: 10px 0 0;
  font-size: 0.85rem;
  color: var(--text-secondary);
}
.swatch {
  width: 11px; height: 11px; border-radius: 3px;
  display: inline-block; margin-right: 6px; vertical-align: -1px;
}
table { border-collapse: collapse; width: 100%; font-size: 0.87rem; }
th, td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid var(--border);
}
th { color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
caption {
  caption-side: bottom;
  color: var(--text-muted);
  font-size: 0.8rem;
  text-align: left;
  padding-top: 10px;
}
.caveat {
  background: var(--surface-raised);
  border: 1px solid var(--border);
  border-left: 3px solid var(--critical);
  border-radius: 8px;
  padding: 14px 16px;
  margin: 20px 0;
  font-size: 0.88rem;
  color: var(--text-secondary);
}
.caveat strong { color: var(--text-primary); }
footer {
  margin-top: 44px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
  font-size: 0.82rem;
  color: var(--text-muted);
}
@media (max-width: 720px) {
  body { padding: 22px 14px 44px; }
  .masthead { display: block; }
  .theme-toggle { margin-top: 16px; }
  .split { grid-template-columns: 1fr; }
  .insight { margin-top: 0; }
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 440px) {
  .tiles { grid-template-columns: 1fr; }
}
"""


def legend() -> str:
    """Legenda das duas modalidades."""
    items = "".join(
        f'<span><span class="swatch" '
        f'style="background: var(--series-{modality})"></span>'
        f"{MODALITY_LABELS[modality]}</span>"
        for modality in (1, 2)
    )
    return f'<div class="legend">{items}</div>'


SERIES_QUERY = """
SELECT census_year, teaching_modality,
       SUM(offered_seats) AS seats,
       SUM(entrants) AS entrants
FROM analytics.course_supply_snapshot
GROUP BY census_year, teaching_modality
ORDER BY census_year, teaching_modality
"""

INSTITUTIONS_QUERY = """
SELECT supply.institution_id,
       COALESCE(inst.institution_name, 'IES ' || supply.institution_id)
           AS institution_name,
       inst.institution_state,
       SUM(supply.offered_seats - supply.entrants) AS unconverted,
       SUM(supply.entrants)::NUMERIC
           / NULLIF(SUM(supply.offered_seats), 0) AS occupancy,
       COUNT(*) AS offers
FROM analytics.course_supply_snapshot AS supply
LEFT JOIN staging.institutions AS inst
    USING (census_year, institution_id)
WHERE supply.census_year = %(year)s
  AND supply.offered_seats > 0
GROUP BY 1, 2, 3
ORDER BY unconverted DESC
LIMIT %(limit)s
"""

CONCENTRATION_QUERY = """
WITH per_institution AS (
    SELECT institution_id,
           SUM(offered_seats - entrants) AS unconverted
    FROM analytics.course_supply_snapshot
    WHERE census_year = %(year)s AND offered_seats > 0
    GROUP BY institution_id
),
ranked AS (
    SELECT unconverted,
           SUM(unconverted) OVER (
               ORDER BY unconverted DESC ROWS UNBOUNDED PRECEDING
           ) AS running,
           SUM(unconverted) OVER () AS total,
           ROW_NUMBER() OVER (ORDER BY unconverted DESC) AS position
    FROM per_institution
)
SELECT position, running::NUMERIC / total AS cumulative_share
FROM ranked
WHERE position IN (1, 5, 10, 20, 50)
ORDER BY position
"""

PERSISTENCE_QUERY = """
SELECT teaching_modality,
       COUNT(*) AS offers,
       AVG(low_occupancy_share) AS mean_low_share,
       COUNT(*) FILTER (WHERE low_occupancy_share = 1)::NUMERIC
           / COUNT(*) AS always_idle_share,
       COUNT(*) FILTER (WHERE current_low_occupancy_streak >= 5)::NUMERIC
           / COUNT(*) AS long_streak_share,
       AVG(demand_volatility) AS mean_volatility
FROM analytics.course_persistence
WHERE measurable_years >= 8 AND NOT has_gaps
GROUP BY teaching_modality
ORDER BY teaching_modality
"""

TOTALS_QUERY = """
SELECT COUNT(DISTINCT institution_id) AS institutions,
       SUM(offered_seats - entrants) AS unconverted,
       SUM(offered_seats) AS seats
FROM analytics.course_supply_snapshot
WHERE census_year = %(year)s AND offered_seats > 0
"""

TRANSITION_QUERY = """
WITH first_year AS (
    SELECT *
    FROM analytics.modality_portfolio_state
    WHERE census_year = (
        SELECT MIN(census_year) FROM analytics.course_supply_snapshot
    )
),
last_year AS (
    SELECT *
    FROM analytics.modality_portfolio_state
    WHERE census_year = %(year)s
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
    COUNT(*) AS surviving_pairs,
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
WITH current_offers AS (
    SELECT teaching_modality, COUNT(*) AS offers
    FROM analytics.course_supply_snapshot
    WHERE census_year = %(year)s AND graduates IS NOT NULL
    GROUP BY teaching_modality
)
SELECT
    summary.teaching_modality,
    summary.eligible_offers,
    summary.eligible_offers::NUMERIC
        / NULLIF(current_offers.offers, 0) AS coverage_share,
    summary.aggregate_completion_ratio,
    summary.median_offer_ratio,
    summary.exceeds_one_share
FROM analytics.lagged_completion_summary AS summary
JOIN current_offers USING (teaching_modality)
WHERE summary.census_year = %(year)s
  AND summary.lag_years = 4
ORDER BY summary.teaching_modality
"""


def render_table(headers: list[str], rows: list[list[str]], caption: str) -> str:
    """Renderiza uma tabela com legenda explicativa."""
    numeric = [index for index, name in enumerate(headers) if name.startswith("#")]
    head = "".join(
        f'<th class="num">{escape(name[1:])}</th>'
        if index in numeric
        else f"<th>{escape(name)}</th>"
        for index, name in enumerate(headers)
    )
    body = "".join(
        "<tr>"
        + "".join(
            f'<td class="num">{escape(cell)}</td>'
            if index in numeric
            else f"<td>{escape(cell)}</td>"
            for index, cell in enumerate(row)
        )
        + "</tr>"
        for row in rows
    )
    return (
        f"<table><caption>{escape(caption)}</caption>"
        f"<thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    )


def _score_columns(feature_columns: list[str]) -> list[str]:
    """Combina identificadores e atributos sem repetir nomes."""
    return list(
        dict.fromkeys(
            [
                "institution_id",
                "course_id",
                "reference_year",
                *feature_columns,
            ]
        )
    )


def load_dashboard_data(year: int = 2024, top: int = 12) -> dict:
    """Lê do PostgreSQL tudo o que o painel mostra."""
    import pandas as pd
    from sqlalchemy import create_engine, text

    from radar_sustentabilidade.alerting import (
        FEATURE_COLUMNS,
        LABEL_COLUMN,
        SPLIT_COLUMN,
        score_year,
    )
    from radar_sustentabilidade.config import Settings

    engine = create_engine(Settings().database_url)
    try:
        with engine.connect() as connection:
            series = pd.read_sql(text(SERIES_QUERY), connection)
            institutions = pd.read_sql(
                text(INSTITUTIONS_QUERY.replace("%(year)s", ":year")
                     .replace("%(limit)s", ":limit")),
                connection,
                params={"year": year, "limit": top},
            )
            concentration = pd.read_sql(
                text(CONCENTRATION_QUERY.replace("%(year)s", ":year")),
                connection,
                params={"year": year},
            )
            persistence = pd.read_sql(text(PERSISTENCE_QUERY), connection)
            totals = pd.read_sql(
                text(TOTALS_QUERY.replace("%(year)s", ":year")),
                connection,
                params={"year": year},
            )
            transition = pd.read_sql(
                text(TRANSITION_QUERY.replace("%(year)s", ":year")),
                connection,
                params={"year": year},
            )
            completion = pd.read_sql(
                text(COMPLETION_QUERY.replace("%(year)s", ":year")),
                connection,
                params={"year": year},
            )

            selected_columns = _score_columns(FEATURE_COLUMNS)
            columns = ", ".join(selected_columns)
            scoring_columns = ", ".join(
                f"features.{column}"
                for column in selected_columns
            )
            labelled = pd.read_sql(
                text(
                    f"SELECT {columns}, {LABEL_COLUMN}, {SPLIT_COLUMN} "
                    "FROM analytics.offer_training_set"
                ),
                connection,
            )
            scoring = pd.read_sql(
                text(
                    f"SELECT {scoring_columns}, snapshot.course_name "
                    "FROM analytics.offer_features AS features "
                    "JOIN analytics.course_supply_snapshot AS snapshot "
                    "  ON snapshot.institution_id = features.institution_id "
                    " AND snapshot.course_id = features.course_id "
                    " AND snapshot.teaching_modality = "
                    "features.teaching_modality "
                    " AND snapshot.census_year = features.reference_year "
                    "WHERE features.reference_year = :year "
                    "AND features.enrollments >= 20"
                ),
                connection,
                params={"year": year},
            )
            names = pd.read_sql(
                text(
                    "SELECT institution_id, institution_name, "
                    "institution_state FROM staging.institutions "
                    "WHERE census_year = :year"
                ),
                connection,
                params={"year": year},
            )
    finally:
        engine.dispose()

    scoring = scoring.copy()
    scoring["risk"] = score_year(labelled, scoring)
    scoring = scoring.merge(names, on="institution_id", how="left")
    alerts = (
        scoring.sort_values("risk", ascending=False)
        .drop_duplicates("institution_id")
        .head(15)
    )

    points = [
        Point(
            year=int(row.census_year),
            modality=int(row.teaching_modality),
            seats=int(row.seats),
            entrants=int(row.entrants),
            occupancy=float(row.entrants) / float(row.seats)
            if row.seats
            else 0.0,
        )
        for row in series.itertuples()
    ]

    return {
        "year": year,
        "points": points,
        "institutions": institutions.to_dict("records"),
        "concentration": concentration.to_dict("records"),
        "persistence": persistence.to_dict("records"),
        "totals": totals.to_dict("records")[0],
        "transition": transition.to_dict("records")[0],
        "completion": completion.to_dict("records"),
        "alerts": alerts.to_dict("records"),
    }


def _point(points: list[Point], year: int, modality: int) -> Point:
    for point in points:
        if point.year == year and point.modality == modality:
            return point
    raise ValueError(f"Série sem modalidade {modality} no ano {year}")


def _persistence_rows(rows: list[dict]) -> list[dict]:
    by_modality = {
        int(row["teaching_modality"]): row
        for row in rows
    }
    missing = {1, 2} - set(by_modality)
    if missing:
        raise ValueError(f"Persistência sem modalidades: {sorted(missing)}")
    return [
        {
            "label": "Anos com baixa ocupação",
            1: float(by_modality[1]["mean_low_share"]),
            2: float(by_modality[2]["mean_low_share"]),
            "maximum": 0.6,
            "fmt": format_percent,
        },
        {
            "label": "Sempre abaixo de 25%",
            1: float(by_modality[1]["always_idle_share"]),
            2: float(by_modality[2]["always_idle_share"]),
            "maximum": 0.25,
            "fmt": format_percent,
        },
        {
            "label": "Sequência de 5+ anos",
            1: float(by_modality[1]["long_streak_share"]),
            2: float(by_modality[2]["long_streak_share"]),
            "maximum": 0.35,
            "fmt": format_percent,
        },
    ]


def _alert_rows(alerts: list[dict]) -> list[list[str]]:
    rows = []
    for position, row in enumerate(alerts, start=1):
        institution = row.get("institution_name") or f"IES {row['institution_id']}"
        state = row.get("institution_state") or "—"
        rows.append(
            [
                str(position),
                str(institution),
                state,
                str(row.get("course_name") or f"Curso {row['course_id']}"),
                MODALITY_LABELS[int(row["teaching_modality"])],
                format_integer(int(row["enrollments"])),
            ]
        )
    return rows


def render_dashboard(data: dict) -> str:
    """Monta o painel completo como um documento HTML autocontido."""
    points = data["points"]
    if not points:
        raise ValueError("O painel exige uma série temporal")

    year = int(data["year"])
    first_year = min(point.year for point in points)
    current = [_point(points, year, modality) for modality in (1, 2)]
    first = [_point(points, first_year, modality) for modality in (1, 2)]
    current_seats = sum(point.seats for point in current)
    current_entrants = sum(point.entrants for point in current)
    first_seats = sum(point.seats for point in first)
    first_entrants = sum(point.entrants for point in first)
    total_occupancy = current_entrants / current_seats
    first_occupancy = first_entrants / first_seats

    totals = data["totals"]
    concentration = {
        int(row["position"]): float(row["cumulative_share"])
        for row in data["concentration"]
    }
    persistence = {
        int(row["teaching_modality"]): row
        for row in data["persistence"]
    }
    transition = data["transition"]

    tiles = "".join(
        [
            stat_tile(
                format_millions(current_seats),
                f"Vagas declaradas em {year}",
                f"{format_ratio(current_seats / first_seats)} "
                f"o volume de {first_year}",
            ),
            stat_tile(
                format_millions(current_entrants),
                f"Ingressantes em {year}",
                f"{(current_entrants / first_entrants - 1):.0%} desde {first_year}",
            ),
            stat_tile(
                format_percent(total_occupancy),
                "Ocupação geral",
                f"{format_percent(first_occupancy)} em {first_year}",
            ),
            stat_tile(
                format_millions(float(totals["unconverted"])),
                "Vagas não convertidas",
                f"{format_integer(int(totals['institutions']))} IES com capacidade",
            ),
        ]
    )

    institution_rows = [
        [
            str(row["institution_name"]),
            str(row.get("institution_state") or "—"),
            format_millions(float(row["unconverted"])),
            format_percent(float(row["occupancy"])),
        ]
        for row in data["institutions"]
    ]
    persistence_table = [
        [
            MODALITY_LABELS[modality],
            format_integer(int(persistence[modality]["offers"])),
            format_percent(float(persistence[modality]["mean_low_share"])),
            format_percent(float(persistence[modality]["mean_volatility"])),
        ]
        for modality in (1, 2)
    ]
    seats_chart = line_chart(
        points,
        "seats",
        "Vagas declaradas por modalidade",
        format_millions,
    )
    occupancy_chart = line_chart(
        points,
        "occupancy",
        "Ocupação por modalidade",
        format_percent,
        y_max=0.55,
    )
    institution_chart = ranked_bars(
        data["institutions"],
        "unconverted",
        "institution_name",
    )
    institution_table = render_table(
        ["Instituição", "UF", "#Vagas não convertidas", "#Ocupação"],
        institution_rows,
        (
            "Ranking de capacidade declarada não convertida em ingressantes; "
            f"ano de referência {year}."
        ),
    )
    persistence_chart = paired_bars(_persistence_rows(data["persistence"]))
    persistence_table_html = render_table(
        ["Modalidade", "#Ofertas no painel", "#Anos ociosos", "#Volatilidade"],
        persistence_table,
        "Volatilidade é o coeficiente de variação dos ingressantes.",
    )
    completion_rows = [
        [
            MODALITY_LABELS[int(row["teaching_modality"])],
            format_integer(int(row["eligible_offers"])),
            format_percent(float(row["coverage_share"])),
            format_percent(float(row["aggregate_completion_ratio"])),
            format_percent(float(row["median_offer_ratio"])),
            format_percent(float(row["exceeds_one_share"])),
        ]
        for row in data["completion"]
    ]
    completion_table = render_table(
        [
            "Modalidade",
            "#Ofertas elegíveis",
            "#Cobertura",
            "#Razão agregada",
            "#Mediana",
            "#Acima de 100%",
        ],
        completion_rows,
        (
            "Concluintes em 2024 sobre ingressantes da mesma oferta em 2020; "
            "mínimo de 20 ingressantes no ano-base."
        ),
    )
    alert_table = render_table(
        [
            "#Prioridade",
            "Instituição",
            "UF",
            "Curso",
            "Modalidade",
            "#Matrículas",
        ],
        _alert_rows(data["alerts"]),
        f"Ranking prospectivo; o horizonte de {year} ainda não possui rótulo.",
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description"
        content="Sustentabilidade da oferta de educação superior, 2014 a 2024.">
  <title>Radar de Sustentabilidade da Educação Superior</title>
  <style>{STYLE}</style>
</head>
<body>
<main class="wrap">
  <header class="masthead">
    <div>
      <p class="eyebrow">Censo da Educação Superior · 2014–{year}</p>
      <h1>Radar de Sustentabilidade da Educação Superior</h1>
      <p class="subtitle">
        Onde a oferta cresce sem converter capacidade em ingressantes — e quais
        cursos apresentam sinais antecipados de deterioração.
      </p>
    </div>
    <button class="theme-toggle" type="button" onclick="toggleTheme()"
            aria-label="Alternar tema">Alternar tema</button>
  </header>

  <section aria-labelledby="panorama">
    <p class="section-kicker">Panorama nacional</p>
    <h2 id="panorama">A capacidade quase triplicou; a ocupação recuou</h2>
    <p class="lede">
      A leitura combina escala, conversão e persistência. Vagas são capacidade
      declarada no Censo, não necessariamente capacidade física.
    </p>
    <div class="tiles">{tiles}</div>
    <div class="split">
      <div>
        <h2>Expansão por modalidade</h2>
        <p class="lede">
          Praticamente toda a expansão veio da EAD; o volume presencial
          permaneceu estável.
        </p>
        <div class="panel">{seats_chart}</div>
        {legend()}
      </div>
      <aside class="insight">
        <p>
          <strong>
            EAD: {format_ratio(current[1].seats / first[1].seats)} mais vagas.
          </strong>
        </p>
        <p>
          De {format_millions(first[1].seats)} para
          {format_millions(current[1].seats)}, enquanto o presencial passou de
          {format_millions(first[0].seats)} para
          {format_millions(current[0].seats)}.
        </p>
      </aside>
    </div>
    <h2>Conversão da capacidade</h2>
    <p class="lede">
      Ingressantes divididos por vagas declaradas. A distância entre
      modalidades persiste em toda a série.
    </p>
    <div class="panel">{occupancy_chart}</div>
    {legend()}
  </section>

  <section aria-labelledby="concentracao">
    <p class="section-kicker">Priorização</p>
    <h2 id="concentracao">A capacidade não convertida está concentrada</h2>
    <p class="lede">
      Poucas instituições cobrem grande parte do fenômeno, tornando uma
      auditoria focalizada mais eficiente que uma varredura censitária.
    </p>
    <div class="tiles">
      {stat_tile(format_percent(concentration[1]), "1 IES", "Participação acumulada")}
      {stat_tile(format_percent(concentration[10]), "10 IES", "Participação acumulada")}
      {stat_tile(format_percent(concentration[50]), "50 IES", "Participação acumulada")}
    </div>
    <div class="panel">{institution_chart}</div>
    <div class="panel">{institution_table}</div>
    <div class="caveat">
      <strong>Como interpretar:</strong> vaga declarada pode representar teto
      regulatório ou comercial. O ranking identifica escala de não conversão;
      não prova ineficiência financeira nem falta de estrutura.
    </div>
  </section>

  <section aria-labelledby="persistencia">
    <p class="section-kicker">Diagnóstico longitudinal</p>
    <h2 id="persistencia">A baixa ocupação da EAD é persistente</h2>
    <p class="lede">
      Ofertas com ao menos oito anos mensuráveis e sem lacunas. Baixa ocupação
      significa menos de 25% das vagas convertidas em ingressantes.
    </p>
    <div class="panel">{persistence_chart}</div>
    {legend()}
    <div class="panel">{persistence_table_html}</div>
    <div class="caveat">
      <strong>Viés de sobrevivência:</strong> somente 12,3% das ofertas EAD
      possuem oito anos ou mais, contra 50,2% do presencial. O painel longo da
      EAD é um subconjunto de ofertas sobreviventes.
    </div>
  </section>

  <section aria-labelledby="transicao">
    <p class="section-kicker">Estrutura do portfólio</p>
    <h2 id="transicao">Expansão da EAD não significa substituição direta</h2>
    <p class="lede">
      A comparação usa IES × área CINE, uma unidade comum às duas modalidades,
      e acompanha somente os portfólios presentes em {first_year} e {year}.
    </p>
    <div class="tiles">
      {stat_tile(
          format_percent(current[1].seats / current_seats),
          "Participação EAD nas vagas",
          f"{format_percent(first[1].seats / first_seats)} em {first_year}",
      )}
      {stat_tile(
          format_percent(current[1].entrants / current_entrants),
          "Participação EAD nos ingressantes",
          "Conversão cresce menos que capacidade",
      )}
      {stat_tile(
          format_percent(float(transition["substitution_signal_share"])),
          "Sinal de substituição",
          f"{format_integer(int(transition['surviving_pairs']))} pares sobreviventes",
      )}
      {stat_tile(
          format_decimal(float(transition["seat_change_correlation"])),
          "Correlação das variações",
          "EAD versus presencial",
      )}
    </div>
    <div class="caveat">
      <strong>Leitura:</strong> a EAD domina a expansão, mas o padrão principal
      é entrada de novos portfólios e dualização. O sinal de substituição é
      descritivo e não identifica efeito causal.
    </div>
  </section>

  <section aria-labelledby="conclusao">
    <p class="section-kicker">Fluxo com defasagem</p>
    <h2 id="conclusao">Conclusão melhora com denominador temporal</h2>
    <p class="lede">
      A referência de quatro anos aproxima entrada e conclusão; a análise
      completa preserva também defasagens de três e cinco anos.
    </p>
    <div class="panel">{completion_table}</div>
    <div class="caveat">
      <strong>Não é taxa de coorte:</strong> o Censo não rastreia indivíduos,
      transferências nem duração específica. Resultados acima de 100% são
      mantidos como diagnóstico de mistura de coortes.
    </div>
  </section>

  <section aria-labelledby="alertas">
    <p class="section-kicker">Ação antecipada</p>
    <h2 id="alertas">Ofertas para auditoria prioritária em {year}</h2>
    <p class="lede">
      Uma oferta por instituição, ordenada pelo sinal do modelo. O evento
      previsto é queda superior a 50% das matrículas ou desaparecimento em
      dois anos.
    </p>
    <div class="panel">{alert_table}</div>
    <div class="caveat">
      <strong>Uso correto:</strong> operar pelo ranking, não por limiar de
      probabilidade. O modelo é superconfiante fora do tempo; a lista limita
      uma oferta por IES para diversificar a capacidade de auditoria.
    </div>
  </section>

  <footer>
    Fonte: Microdados do Censo da Educação Superior, Inep. Elaboração própria.
    Recorte: graduação no Brasil; dimensão exterior excluída.
  </footer>
</main>
<script>
function toggleTheme() {{
  const root = document.documentElement;
  const current = root.dataset.theme;
  root.dataset.theme = current === "dark" ? "light" : "dark";
}}
</script>
</body>
</html>
"""


def write_dashboard(
    output_path: Path,
    year: int = 2024,
    top: int = 12,
) -> Path:
    """Carrega os dados e persiste o painel autocontido."""
    html = render_dashboard(load_dashboard_data(year=year, top=top))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    return output_path
