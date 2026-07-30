import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from radar_sustentabilidade.cli import app
from radar_sustentabilidade.portfolio import (
    REQUIRED_ARTIFACTS,
    build_portfolio_manifest,
    verify_portfolio_manifest,
    write_portfolio_manifest,
)


def make_artifacts(root: Path) -> None:
    for relative in REQUIRED_ARTIFACTS:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if relative.endswith("reports/dashboard/index.html"):
            path.write_text(
                "<!doctype html><h1>Sinal de substituição</h1>"
                "<h2>Conclusão melhora com denominador temporal</h2>"
                "<h2>Ofertas para auditoria prioritária</h2>",
                encoding="utf-8",
            )
        elif relative.endswith("reports/milestone3/metrics.json"):
            path.write_text(
                json.dumps(
                    {
                        "schema_version": 1,
                        "period": {"last_year": 2024},
                    }
                ),
                encoding="utf-8",
            )
        elif relative.endswith("reports/alerting/experiment.json"):
            path.write_text(
                json.dumps(
                    {
                        "evaluations": [
                            {
                                "split": "teste",
                                "roc_auc": 0.81,
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
        else:
            path.write_text(f"# {relative}\n", encoding="utf-8")


def test_manifest_records_every_required_artifact(tmp_path: Path) -> None:
    make_artifacts(tmp_path)

    manifest = build_portfolio_manifest(tmp_path)

    assert manifest["artifact_count"] == len(REQUIRED_ARTIFACTS)
    assert all(manifest["semantic_checks"].values())
    assert {row["path"] for row in manifest["artifacts"]} == set(
        REQUIRED_ARTIFACTS
    )


def test_verification_detects_changed_artifact(tmp_path: Path) -> None:
    make_artifacts(tmp_path)
    manifest_path = tmp_path / "reports/portfolio/manifest.json"
    write_portfolio_manifest(manifest_path, tmp_path)
    (tmp_path / "README.md").write_text("alterado", encoding="utf-8")

    with pytest.raises(ValueError, match="README.md"):
        verify_portfolio_manifest(manifest_path, tmp_path)


def test_manifest_ignores_platform_line_endings(tmp_path: Path) -> None:
    make_artifacts(tmp_path)
    manifest_path = tmp_path / "reports/portfolio/manifest.json"
    write_portfolio_manifest(manifest_path, tmp_path)
    readme = tmp_path / "README.md"
    normalized = readme.read_bytes().replace(b"\r\n", b"\n")
    readme.write_bytes(normalized.replace(b"\n", b"\r\n"))

    result = verify_portfolio_manifest(manifest_path, tmp_path)

    assert result["valid"] is True


def test_verify_portfolio_command(tmp_path: Path) -> None:
    make_artifacts(tmp_path)
    manifest_path = tmp_path / "reports/portfolio/manifest.json"
    write_portfolio_manifest(manifest_path, tmp_path)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.chdir(tmp_path)
        result = CliRunner().invoke(
            app,
            ["verify-portfolio", "--manifest", str(manifest_path)],
        )

    assert result.exit_code == 0
    assert "portfólio íntegro" in result.stdout
