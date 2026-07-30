# Mudanças de leiaute entre edições

## Método

Cada edição é baixada, inventariada e perfilada de forma independente (mesmo
pipeline usado em 2024). As colunas do CSV de cursos são comparadas par a par
entre edições consecutivas antes de qualquer união longitudinal. Uma coluna só
é tratada como comparável entre anos quando o nome, a posição relativa e o
dicionário de dados concordam.

## 2023 → 2024

### Estrutura do pacote

| Aspecto | 2023 | 2024 |
|---|---|---|
| Organização interna | Subpastas `Anexos/`, `dados/`, `leia-me/` | Arquivos soltos na raiz do ZIP |
| Artefatos extras | Arquivos de bloqueio do Office (`~$*.xlsx`, `~$*.docx`) | Nenhum |
| Tamanho do ZIP | 38.411.202 bytes | 456.807.449 bytes |
| Linhas — cursos | 671.610 | 720.349 |
| Colunas — cursos | 202 | 223 |
| Linhas — IES | 2.580 | 2.561 |
| Colunas — IES | 84 (idênticas, mesma ordem) | 84 |

O perfil estrutural (`profile_package`) precisou ignorar os arquivos de
bloqueio do Office (`~$...`), que não são membros de dados e não devem contar
como dicionário ou CSV candidato.

### Coluna descontinuada: `QT_*_RVETNICO`

Em 2023, o bloco de reserva de vagas tinha uma única coluna étnica genérica
por métrica:

```text
QT_ING_RESERVA_VAGA, QT_ING_RVREDEPUBLICA, QT_ING_RVETNICO,
QT_ING_RVPDEF, QT_ING_RVSOCIAL_RF, ...
```

Em 2024, `QT_*_RVETNICO` desaparece e, no mesmo ponto do leiaute, entram oito
categorias mais granulares, repetidas para ingressantes, matrículas e
concluintes (24 colunas novas no lugar de 3 antigas):

```text
QT_*_RVPPI, QT_*_RVQUILO, QT_*_RVREFU, QT_*_RVPOVT,
QT_*_RVIDOSO, QT_*_RVINTERN, QT_*_RVMEDAL, QT_*_RVTRANS
```

Isso confirma a nota já registrada em
[2024_quality_findings.md](2024_quality_findings.md): `QT_ING_RVETNICO`,
`QT_MAT_RVETNICO` e `QT_CONC_RVETNICO` são válidas apenas entre 2009 e 2023.

### Implicação para a série histórica

- A soma de `RVETNICO` (2023 e anteriores) não é diretamente comparável à soma
  das oito categorias novas (2024 em diante); qualquer indicador de
  "reserva de vagas por critério étnico/racial" precisa de uma regra de
  reconciliação explícita antes de unir os anos, análoga à reconciliação já
  aplicada para as dimensões da EAD.
- As demais 202 colunas de 2023 aparecem em 2024 com o mesmo nome, mas nem
  sempre na mesma posição relativa — a união entre anos deve ser feita por
  nome de coluna, nunca por posição ordinal.
- O dicionário de 2023 não lista nenhuma variável ausente do CSV nem sobra do
  CSV ausente do dicionário — mais consistente que o de 2024, que lista três
  variáveis inexistentes no cabeçalho real (ver achados de 2024).

## Próximas edições

Cada nova edição incorporada deve repetir esta comparação com a edição mais
recente já perfilada, registrando aqui apenas as mudanças reais de leiaute —
não a lista completa de colunas idênticas entre anos.
