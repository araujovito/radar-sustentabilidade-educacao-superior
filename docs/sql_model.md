# Modelo SQL do MVP

## Camadas

### `raw`

As tabelas raw são geradas diretamente dos cabeçalhos reais dos CSVs. Todas as
colunas entram como `TEXT` para que valores inesperados não sejam convertidos
ou descartados silenciosamente durante a carga.

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

## Execução planejada

1. Gerar o DDL raw:

   ```bash
   radar generate-sql
   ```

2. Executar `sql/generated/010_raw_2024.sql`.
3. Extrair os CSVs do ZIP:

   ```bash
   radar extract-tables caminho/arquivo.zip
   ```

4. A partir da raiz do projeto, executar
   `sql/generated/011_load_2024.psql`.
5. Executar os scripts de staging, analytics e quality na ordem numérica.
