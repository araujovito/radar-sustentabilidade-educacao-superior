"""Interface de linha de comando."""

import typer

from radar_sustentabilidade import __version__

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Comandos do Radar de Sustentabilidade."""


@app.command()
def version() -> None:
    """Exibe a versão instalada."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
