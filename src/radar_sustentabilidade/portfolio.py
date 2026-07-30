"""Empacotamento e verificação da demonstração de portfólio."""

import hashlib
import json
import os
from pathlib import Path

REQUIRED_ARTIFACTS = (
    "README.md",
    "docs/demo.md",
    "docs/executive_report.md",
    "docs/modality_completion_findings.md",
    "reports/alerting/experiment.json",
    "reports/dashboard/index.html",
    "reports/milestone3/metrics.json",
)


def _canonical_bytes(path: Path) -> bytes:
    """Normaliza fins de linha para o manifesto ser portátil."""
    return path.read_bytes().replace(b"\r\n", b"\n")


def _sha256(path: Path) -> str:
    return hashlib.sha256(_canonical_bytes(path)).hexdigest()


def _check_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def semantic_checks(root: Path) -> dict[str, bool]:
    """Verifica propriedades que um arquivo existente, sozinho, não prova."""
    dashboard = (root / "reports/dashboard/index.html").read_text(
        encoding="utf-8"
    )
    milestone3 = _check_json(root / "reports/milestone3/metrics.json")
    alerting = _check_json(root / "reports/alerting/experiment.json")
    evaluations = alerting.get("evaluations", [])

    return {
        "dashboard_is_self_contained": (
            dashboard.startswith("<!doctype html>")
            and "https://" not in dashboard
            and "http://" not in dashboard
        ),
        "dashboard_contains_decision_sections": all(
            title in dashboard
            for title in (
                "Sinal de substituição",
                "Conclusão melhora com denominador temporal",
                "Ofertas para auditoria prioritária",
            )
        ),
        "milestone3_schema_is_supported": (
            milestone3.get("schema_version") == 1
            and milestone3.get("period", {}).get("last_year") == 2024
        ),
        "alert_model_has_temporal_test": any(
            row.get("split") == "teste" and row.get("roc_auc") is not None
            for row in evaluations
        ),
    }


def build_portfolio_manifest(root: Path = Path(".")) -> dict:
    """Calcula o manifesto determinístico dos artefatos publicados."""
    artifacts = []
    for relative in REQUIRED_ARTIFACTS:
        path = root / relative
        if not path.is_file():
            raise FileNotFoundError(f"Artefato obrigatório ausente: {relative}")
        artifacts.append(
            {
                "path": relative,
                "bytes": len(_canonical_bytes(path)),
                "sha256": _sha256(path),
            }
        )

    checks = semantic_checks(root)
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"Verificações semânticas falharam: {failed}")

    return {
        "schema_version": 1,
        "project": "Radar de Sustentabilidade da Educação Superior",
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "semantic_checks": checks,
    }


def write_portfolio_manifest(
    output_path: Path = Path("reports/portfolio/manifest.json"),
    root: Path = Path("."),
) -> Path:
    """Persiste o manifesto de entrega."""
    manifest = build_portfolio_manifest(root)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_path


def verify_portfolio_manifest(
    manifest_path: Path = Path("reports/portfolio/manifest.json"),
    root: Path = Path("."),
) -> dict:
    """Compara os artefatos locais com o manifesto versionado."""
    expected = _check_json(manifest_path)
    failures = []
    for artifact in expected.get("artifacts", []):
        path = root / artifact["path"]
        if not path.is_file():
            failures.append(f"ausente: {artifact['path']}")
            continue
        if len(_canonical_bytes(path)) != artifact["bytes"]:
            failures.append(f"tamanho divergente: {artifact['path']}")
        if _sha256(path) != artifact["sha256"]:
            failures.append(f"hash divergente: {artifact['path']}")

    checks = semantic_checks(root)
    failures.extend(
        f"checagem semântica: {name}"
        for name, passed in checks.items()
        if not passed
    )
    if failures:
        raise ValueError("; ".join(failures))

    return {
        "valid": True,
        "artifact_count": len(expected["artifacts"]),
        "semantic_checks": checks,
    }


def rebuild_portfolio(
    manifest_path: Path = Path("reports/portfolio/manifest.json"),
) -> list[Path]:
    """Reconstrói os produtos derivados do banco e atualiza o manifesto."""
    os.environ.setdefault("LOKY_MAX_CPU_COUNT", str(os.cpu_count() or 1))

    from radar_sustentabilidade.alerting import (
        load_training_set,
        write_experiment_report,
    )
    from radar_sustentabilidade.dashboard import write_dashboard
    from radar_sustentabilidade.milestone3 import write_milestone3_report

    milestone3 = write_milestone3_report()
    alerting = Path("reports/alerting/experiment.json")
    write_experiment_report(load_training_set(), alerting)
    dashboard = write_dashboard(Path("reports/dashboard/index.html"))
    manifest = write_portfolio_manifest(manifest_path)
    return [milestone3, alerting, dashboard, manifest]
