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
            f"{format_integer(row[value_key])} vagas não convertidas</title>"
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
.wrap { max-width: 860px; margin: 0 auto; }
h1 { font-size: 1.6rem; line-height: 1.25; margin: 0 0 6px; }
h2 {
  font-size: 1.08rem;
  margin: 40px 0 4px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
}
.subtitle { color: var(--text-secondary); margin: 0 0 28px; }
.lede { color: var(--text-secondary); margin: 0 0 18px; font-size: 0.95rem; }
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

            columns = ", ".join(
                ["institution_id", "course_id", "teaching_modality",
                 "reference_year", *FEATURE_COLUMNS]
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
                    f"SELECT {columns}, course_name "
                    "FROM analytics.offer_features "
                    "WHERE reference_year = :year AND enrollments >= 20"
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
    alerts = scoring.sort_values("risk", ascending=False).head(15)

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
        "alerts": alerts.to_dict("records"),
    }
