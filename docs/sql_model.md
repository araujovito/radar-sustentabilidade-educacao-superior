# Modelo SQL do MVP

## Camadas

### `raw`

As tabelas raw são geradas diretamente dos cabeçalhos reais dos CSVs. Todas as
colunas entram como `TEXT` para que valores inesperados não sejam convertidos
ou descartados silenciosamente durante a carga.

Cada edição tem sua própria tabela por família:

```text
raw.censo_superior_cursos_{ano}
raw.censo_superior_ies_{ano}
```

O leiaute oficial muda entre anos (ver
[layout_changes.md](layout_changes.md)). Uma tabela por ano preserva o arquivo
como publicado, sem preencher com nulos colunas que não existiam nem descartar
colunas que existiam apenas em uma edição.

### União longitudinal

Sobre as tabelas anuais existem duas views que cobrem 2014 a 2024:

```text
raw.censo_superior_cursos_todos
raw.censo_superior_ies_todos
```

Regras aplicadas na união, geradas a partir dos perfis de cada ano:

- entram apenas colunas presentes em **todas** as edições do recorte — 197 em
  cursos e 81 em IES;
- a união é feita por nome de coluna, nunca por posição ordinal;
- `CO_CINE_ROTULO2`, grafia usada somente no pacote de 2020, é projetada como
  `CO_CINE_ROTULO`;
- colunas de uma única edição ficam fora da união e permanecem acessíveis na
  tabela anual correspondente.

As views são materializadas por `sql/generated/012_raw_longitudinal.sql`, que é
gerado — não editado à mão — para que uma nova edição não exija reescrever a
união:

```bash
radar generate-longitudinal-sql
radar report-layout-drift
```

Estado carregado e verificado no PostgreSQL local: 3.558.875 linhas de cursos
nas onze edições, com as asserções de
`sql/quality/041_assertions_longitudinal.sql` retornando zero.

### `staging`

As views de staging:

- convertem apenas as colunas necessárias ao MVP;
- transformam strings vazias em `NULL`;
- aplicam tipos numéricos explícitos;
- preservam os códigos originais;
- não agregam dimensões geográficas.

### `analytics`

O mart `analytics.course_supply_2024` possui o grão:

```text
ano × IES × curso × modalidade
```

O presencial é agregado a partir da dimensão 1.

No EAD, capacidade e demanda estudantil são reconciliadas:

- vagas, inscrições e quantidade de cursos: dimensão 3;
- ingressantes, matrículas e concluintes: dimensão 2;
- junção: ano, IES, curso e modalidade.

A dimensão 4, referente ao exterior, não participa do MVP.

## Métricas

- `seat_occupancy_rate`: ingressantes divididos por vagas;
- `applications_per_seat`: inscrições divididas por vagas;
- `unconverted_seat_capacity`: vagas menos ingressantes;
- `graduation_intensity`: concluintes divididos por matrículas do mesmo ano.

`graduation_intensity` não é taxa de conclusão de coorte. Ela será usada apenas
como medida transversal até que a série histórica permita construir
denominadores defasados.

## Execução

Para uma edição, com `{ano}` no lugar do ano de referência:

1. Gerar o DDL raw a partir do perfil daquele ano:

   ```bash
   radar generate-sql --profile reports/{ano}/source_profile.json
   ```

2. Executar `sql/generated/010_raw_{ano}.sql`.
3. Extrair os CSVs do ZIP:

   ```bash
   radar extract-tables caminho/arquivo.zip \
     --output-dir data/interim/censo_superior_{ano}
   ```

4. A partir da raiz do projeto, executar
   `sql/generated/011_load_{ano}.psql`.

Depois de carregar todas as edições do recorte:

5. Gerar e executar a união longitudinal:

   ```bash
   radar generate-longitudinal-sql
   ```

6. Executar `sql/generated/012_raw_longitudinal.sql`.
7. Executar os scripts de staging, analytics e quality na ordem numérica.
