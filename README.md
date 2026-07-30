# Radar de Sustentabilidade da Educação Superior

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

## Decisões registradas

- [Recorte analítico inicial](docs/scope.md)
- [Catálogo inicial de fontes](docs/data_catalog.md)
- [Catálogo legível por máquina](config/sources.toml)
- [Achados de qualidade de 2024](docs/2024_quality_findings.md)
- [Modelo SQL do MVP](docs/sql_model.md)
- [Achados analíticos do MVP 2024](docs/mvp_2024_findings.md)
- [Mudanças de leiaute entre edições](docs/layout_changes.md)

## Executar o MVP 2024

Após extrair os dois CSVs do pacote oficial, gere o resumo reproduzível:

```bash
radar build-mvp
```

O comando processa o arquivo de cursos em blocos, reconcilia as dimensões da
EAD e grava `reports/2024/mvp_summary.json`. Os microdados permanecem fora do
Git.
