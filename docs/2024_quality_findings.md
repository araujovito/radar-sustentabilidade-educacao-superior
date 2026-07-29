# Achados de qualidade — Censo Superior 2024

## Integridade do pacote

- Tamanho do ZIP: 456.807.449 bytes.
- SHA-256: `e8e11899efe2b348a7e80e3a3c610c3bdd1ced3362ccdf2c9f9abe9bf8988386`.
- Dez membros no arquivo.
- Dois CSVs em Latin-1, separados por ponto e vírgula.
- Os MD5 dos dois CSVs correspondem ao controle distribuído pelo Inep.

O TXT de controle chama a tabela de IES de
`MICRODADOS_CADASTRO_IES_2024.csv`, enquanto o membro real se chama
`MICRODADOS_ED_SUP_IES_2024.CSV`. O conteúdo corresponde ao hash esperado; a
diferença é de nomenclatura.

## Tabelas

| Tabela | Linhas de dados | Colunas |
|---|---:|---:|
| Cadastro de cursos | 720.349 | 223 |
| Cadastro de IES | 2.561 | 84 |

O dicionário de IES contém exatamente as 84 variáveis do CSV.

O dicionário de cursos lista 226 variáveis. Três não existem no CSV de 2024:
`QT_ING_RVETNICO`, `QT_MAT_RVETNICO` e `QT_CONC_RVETNICO`. As notas do próprio
dicionário dizem que elas são válidas somente entre 2009 e 2023. Entretanto,
as duas últimas estão marcadas com `s` na coluna de coleta de 2024. Para o
pipeline, prevalecerão o cabeçalho real do CSV e a nota de validade.

## Grão

A combinação abaixo é única nas 720.349 linhas:

```text
TP_DIMENSAO + CO_IES + CO_CURSO + CO_MUNICIPIO + TP_MODALIDADE_ENSINO
```

Não foram observadas linhas pertencentes a chaves duplicadas nesse recorte.

## Dimensões e risco de dupla contagem

| `TP_DIMENSAO` | Interpretação | Linhas | Geografia completa |
|---:|---|---:|---:|
| 1 | Presencial no Brasil | 34.824 | 34.824 |
| 2 | Alunos EAD por localidade no Brasil | 673.756 | 673.747 |
| 3 | Oferta EAD em nível nacional | 11.319 | 0 |
| 4 | EAD de IES brasileiras no exterior | 450 | 0 |

As medidas não podem ser somadas indiscriminadamente entre dimensões:

- dimensão 1 contém vagas, ingressantes, matrículas e concluintes presenciais;
- dimensão 2 concentra ingressantes, matrículas e concluintes EAD por
  localidade, mas não a oferta nacional de vagas;
- dimensão 3 concentra cursos, vagas e inscrições EAD em nível nacional, mas
  não os totais de alunos;
- dimensão 4 representa oferta no exterior e fica fora do MVP brasileiro.

## Regra para o mart analítico

Para presencial, usar a dimensão 1.

Para EAD:

1. agregar ingressantes, matrículas e concluintes da dimensão 2 por IES e
   curso;
2. obter vagas, inscrições e quantidade de cursos da dimensão 3;
3. juntar as duas partes por ano, IES, curso e modalidade;
4. manter a dimensão 4 em tabela separada;
5. não somar as dimensões 2 e 3 como se fossem observações equivalentes.
