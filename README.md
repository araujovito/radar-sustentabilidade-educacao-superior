# Radar de Sustentabilidade da Educação Superior

[![verificacao](https://github.com/araujovito/radar-sustentabilidade-educacao-superior/actions/workflows/verificacao.yml/badge.svg)](https://github.com/araujovito/radar-sustentabilidade-educacao-superior/actions/workflows/verificacao.yml)

Projeto analítico em Python e SQL para investigar a capacidade, a conversão, a
eficiência e a sustentabilidade da oferta de educação superior no Brasil.

## Problema

A expansão de vagas não significa, isoladamente, expansão sustentável. Este
projeto busca identificar onde a oferta consegue converter capacidade em
ingressantes, permanência e conclusão, além de reconhecer sinais de
deterioração antes que apareçam nos indicadores mais óbvios.

Pergunta central:

> Onde a oferta de cursos superiores cresce sem converter vagas em alunos,
> permanência e concluintes, e quais sinais antecipam uma deterioração?

## Entregas planejadas

- pipeline reproduzível para obtenção e validação dos dados oficiais;
- banco analítico PostgreSQL com histórico por instituição, curso e ano;
- métricas documentadas de ocupação, eficiência, concentração e volatilidade;
- análise exploratória orientada por hipóteses;
- modelo temporal de alerta de risco, sem vazamento de informação;
- painel de decisão com explicações por curso e instituição.

## Fontes oficiais

- Microdados do Censo da Educação Superior — Inep;
- Indicadores de fluxo e trajetória da educação superior — Inep;
- indicadores de qualidade, como Enade, IDD e CPC, quando o cruzamento for
  metodologicamente válido;
- dados cadastrais do sistema e-MEC, como fonte complementar.

Os arquivos brutos não serão armazenados no GitHub. O pipeline registrará URL,
data de obtenção, tamanho e checksum de cada arquivo.

## Arquitetura inicial

```text
fonte oficial
    -> data/raw
    -> validação e padronização em Python
    -> PostgreSQL: raw
    -> PostgreSQL: staging
    -> PostgreSQL: analytics
    -> notebooks, modelos e painel
```

## Estrutura

```text
data/          dados locais ignorados pelo Git
docs/          decisões analíticas e metodologia
sql/           schemas, transformações e consultas
src/           pacote Python do projeto
tests/         testes automatizados
```

## Início rápido

Requisitos: Python 3.11 ou superior, Docker e Docker Compose.

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
docker compose up -d db
pytest
```

Copie `.env.example` para `.env` antes de executar componentes que acessam o
banco. As credenciais fornecidas são apenas para desenvolvimento local.

## Aquisição reproduzível

Para baixar a fonte catalogada de 2024:

```bash
radar download inep_censo_superior_microdados_2024
```

O comando grava o ZIP, o SHA-256 e os metadados em `data/raw`, que não é
versionado. Para validar e inventariar um ZIP sem extrair seus membros:

```bash
radar inventory caminho/arquivo.zip
```

Se o arquivo foi obtido manualmente:

```bash
radar import-file inep_censo_superior_microdados_2024 caminho/arquivo.zip
```

## Princípios analíticos

- separar descrição, previsão e inferência causal;
- evitar conclusões individuais a partir de dados agregados;
- usar validação temporal nos modelos preditivos;
- documentar denominadores, defasagens e limitações de cada métrica;
- manter todas as transformações reproduzíveis.

O planejamento detalhado está em [ROADMAP.md](ROADMAP.md).

## Resultado

O [relatório executivo](docs/executive_report.md) consolida os achados da série
2014-2024 e o desempenho do sistema de alerta, com as limitações que mudam a
leitura dos números.

## Decisões registradas

- [Recorte analítico inicial](docs/scope.md)
- [Catálogo inicial de fontes](docs/data_catalog.md)
- [Catálogo legível por máquina](config/sources.toml)
- [Achados de qualidade de 2024](docs/2024_quality_findings.md)
- [Modelo SQL do MVP](docs/sql_model.md)
- [Achados analíticos do MVP 2024](docs/mvp_2024_findings.md)
- [Mudanças de leiaute entre edições](docs/layout_changes.md)
- [Persistência e volatilidade na série 2014-2024](docs/persistence_findings.md)
- [Sistema de alerta de deterioração](docs/alerting_findings.md)

## Executar o MVP 2024

Após extrair os dois CSVs do pacote oficial, gere o resumo reproduzível:

```bash
radar build-mvp
```

O comando processa o arquivo de cursos em blocos, reconcilia as dimensões da
EAD e grava `reports/2024/mvp_summary.json`. Os microdados permanecem fora do
Git.

## Verificação automatizada

Cada push executa dois trabalhos no GitHub Actions:

- **qualidade** — `ruff` e `pytest` em Python 3.11 e 3.12;
- **sql** — sobe um PostgreSQL 17, aplica todos os esquemas e views na ordem de
  dependência, carrega um fixture sintético e confere o comportamento.

O fixture em `sql/fixtures` não são dados do Inep: são poucas ofertas
construídas para exercitar o que erra em silêncio — reconciliação das
dimensões da EAD, exclusão da oferta no exterior, normalização da grafia
divergente de 2020, rotulagem por queda de matrículas e por desaparecimento, e
ausência de informação futura nos atributos. Um banco vazio faria as consultas
passarem vaziamente, provando apenas que o SQL compila.

Para reproduzir localmente, com as variáveis do libpq apontando para o banco:

```bash
scripts/build_database.sh --fixture
```

Os arquivos de `sql/quality` são diagnósticos: imprimem contagens sobre a base
completa para leitura humana e não interrompem em divergência. Eles não
substituem o gate automatizado, e a verificação de integridade dos dados
oficiais continua sendo manual, porque os microdados não são versionados.

## Treinar o modelo de alerta

Com a série 2014-2024 carregada no PostgreSQL:

```bash
radar train-alert-model
```

O comando lê `analytics.offer_training_set`, treina com separação cronológica,
avalia fora do tempo e grava `reports/alerting/experiment.json`. Os achados
estão em [alerting_findings.md](docs/alerting_findings.md).
