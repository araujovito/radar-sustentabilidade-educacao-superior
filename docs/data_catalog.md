# Catálogo inicial de fontes

## Fonte primária

| Campo | Valor |
|---|---|
| Órgão | Inep |
| Conjunto | Microdados do Censo da Educação Superior |
| Ano inicial do MVP | 2024 |
| Formato de distribuição | ZIP |
| Página oficial | <https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-da-educacao-superior> |
| Pacote de 2024 | <https://download.inep.gov.br/microdados/microdados_censo_da_educacao_superior_2024.zip> |
| Papel no projeto | Fonte primária de oferta, instituições, cursos e fluxo agregado |

O catálogo legível por máquina está em `config/sources.toml`.

## Documentação

A documentação acompanha o pacote oficial. Na primeira aquisição, o pipeline
deverá inventariar todos os membros do ZIP e identificar:

- dicionário de dados;
- leiautes e legendas;
- notas de leitura;
- arquivos de microdados;
- formato, codificação, separador e compressão;
- tamanho e SHA-256 de cada membro.

Os nomes internos não são fixados neste catálogo antes da inspeção do pacote.
Isso evita acoplar o pipeline a nomes presumidos.

## Série histórica planejada

A página oficial disponibiliza edições anteriores, incluindo todo o intervalo
de 2014 a 2024. O padrão de download registrado é:

```text
https://download.inep.gov.br/microdados/
microdados_censo_da_educacao_superior_{year}.zip
```

Cada ano será tratado como uma versão independente. O padrão de URL não será
usado como evidência de compatibilidade entre leiautes.

## Metadados pendentes da aquisição

- tamanho efetivamente recebido;
- cabeçalhos HTTP disponíveis;
- SHA-256 do ZIP;
- lista e hashes dos membros;
- data e hora da obtenção;
- codificação e separador dos arquivos tabulares.

Esses campos serão produzidos pelo pipeline, e não preenchidos manualmente.
