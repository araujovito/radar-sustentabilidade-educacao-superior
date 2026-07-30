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

### `staging` longitudinal

`staging.courses` e `staging.institutions` — sem sufixo de ano — cobrem 2014 a
2024 lendo as uniões de `raw`. O ano é uma coluna, não um nome de objeto.

Duas diferenças em relação às views de 2024:

- `staging.courses` expõe `education_network`, tipada de `TP_REDE` do arquivo
  de cursos, presente em todas as edições;
- `staging.institutions` **não** expõe `education_network`, porque `TP_REDE`
  só entra no arquivo de IES em 2023. Quem precisa de rede em toda a série usa
  a view de cursos.

A tipagem foi verificada nas 3.558.875 linhas: nenhuma chave se perde em
nenhuma edição. As asserções ficam em
`sql/quality/042_assertions_staging_longitudinal.sql`.

Uma mudança de convenção em 2020 — medidas inaplicáveis a uma dimensão passam
de campo vazio para zero — está documentada em
[layout_changes.md](layout_changes.md) e coberta por asserção. Ela não afeta as
métricas do MVP, mas afeta qualquer média ou contagem calculada sem filtrar
dimensão.

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

### `analytics` longitudinal

`analytics.course_supply` aplica ano a ano a mesma reconciliação validada em
2024. A equivalência é verificada, não presumida: uma asserção compara o
recorte de 2024 do mart longitudinal com `analytics.course_supply_2024` nas
duas direções e exige diferença vazia.

Como as views reconstroem a união das onze edições a cada consulta, o resultado
é materializado em `analytics.course_supply_snapshot` (439.353 ofertas-ano, com
índices pelas chaves do painel). O painel e as métricas de persistência leem a
materialização; reconstruir a união a cada consulta torna o uso interativo
inviável.

Sobre ela ficam:

- `analytics.course_supply_panel`: uma linha por oferta e ano, com ocupação e
  as marcas `has_measurable_occupancy` e `is_low_occupancy`;
- `analytics.course_persistence`: uma linha por oferta, com anos ociosos,
  sequência ociosa atual, volatilidade da demanda e cobertura do painel.

Ofertas com zero vagas declaradas ficam fora do cálculo de ociosidade: são não
mensuráveis, não ociosas. Os achados estão em
[persistence_findings.md](persistence_findings.md).

Reconstruir depois de recarregar qualquer edição:

```bash
psql -f sql/analytics/033_materialize_supply.sql
```

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
