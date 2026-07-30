# Mudanças de leiaute entre edições

## Método

Cada edição é baixada, inventariada e perfilada de forma independente (mesmo
pipeline usado em 2024). As colunas do CSV de cursos são comparadas par a par
entre edições consecutivas antes de qualquer união longitudinal. Uma coluna só
é tratada como comparável entre anos quando o nome, a posição relativa e o
dicionário de dados concordam.

## Cobertura da série

Onze edições adquiridas, cada uma com checksum, manifesto e perfil próprios
(`reports/{ano}/source_profile.json`). O MD5 de todas as tabelas confere com o
controle distribuído pelo Inep.

| Ano | Tabela de cursos | Linhas | Colunas | Tabela de IES | Linhas | Colunas |
|---:|---|---:|---:|---|---:|---:|
| 2014 | `MICRODADOS_CADASTRO_CURSOS_2014` | 73.569 | 200 | `MICRODADOS_CADASTRO_IES_2014` | 2.368 | 81 |
| 2015 | `MICRODADOS_CADASTRO_CURSOS_2015` | 81.156 | 200 | `MICRODADOS_CADASTRO_IES_2015` | 2.364 | 81 |
| 2016 | `MICRODADOS_CADASTRO_CURSOS_2016` | 92.866 | 200 | `MICRODADOS_CADASTRO_IES_2016` | 2.407 | 81 |
| 2017 | `MICRODADOS_CADASTRO_CURSOS_2017` | 119.798 | 200 | `MICRODADOS_CADASTRO_IES_2017` | 2.448 | 81 |
| 2018 | `MICRODADOS_CADASTRO_CURSOS_2018` | 182.892 | 200 | `MICRODADOS_CADASTRO_IES_2018` | 2.537 | 81 |
| 2019 | `MICRODADOS_CADASTRO_CURSOS_2019` | 253.139 | 200 | `MICRODADOS_CADASTRO_IES_2019` | 2.608 | 81 |
| 2020 | `MICRODADOS_CADASTRO_CURSOS_2020` | 344.691 | 200 | `MICRODADOS_CADASTRO_IES_2020` | 2.457 | 81 |
| 2021 | `MICRODADOS_CADASTRO_CURSOS_2021` | 444.786 | 200 | `MICRODADOS_CADASTRO_IES_2021` | 2.574 | 84 |
| 2022 | `MICRODADOS_CADASTRO_CURSOS_2022` | 573.019 | 200 | `MICRODADOS_ED_SUP_IES_2022` | 2.595 | 81 |
| 2023 | `MICRODADOS_CADASTRO_CURSOS_2023` | 671.610 | 202 | `MICRODADOS_ED_SUP_IES_2023` | 2.580 | 84 |
| 2024 | `MICRODADOS_CADASTRO_CURSOS_2024` | 720.349 | 223 | `MICRODADOS_ED_SUP_IES_2024` | 2.561 | 84 |

A tabela de IES muda de nome em 2022: `MICRODADOS_CADASTRO_IES_{ano}` passa a
`MICRODADOS_ED_SUP_IES_{ano}`. O pipeline deve localizar as tabelas por
conteúdo e padrão, nunca por nome fixo.

As linhas de cursos crescem de 73.569 para 720.349 — quase dez vezes. Isso é
expansão da EAD por localidade (dimensão 2), não crescimento equivalente da
oferta: a dimensão 1 (presencial) vai apenas de 31.905 a 34.824 no mesmo
intervalo.

## Estabilidade das dimensões

`TP_DIMENSAO` existe em todas as onze edições, com a mesma semântica usada na
reconciliação de 2024. A dimensão 4 (EAD de IES brasileiras no exterior) só
passa a existir em 2017:

| Ano | Dim. 1 | Dim. 2 | Dim. 3 | Dim. 4 |
|---:|---:|---:|---:|---:|
| 2014 | 31.905 | 40.296 | 1.368 | — |
| 2015 | 32.397 | 47.283 | 1.476 | — |
| 2016 | 33.031 | 58.171 | 1.664 | — |
| 2017 | 33.581 | 84.085 | 2.112 | 20 |
| 2018 | 35.076 | 144.549 | 3.180 | 87 |
| 2021 | 35.750 | 401.088 | 7.624 | 324 |
| 2022 | 36.089 | 527.328 | 9.207 | 395 |

A regra de reconciliação da EAD (vagas e inscrições da dimensão 3; alunos da
dimensão 2; dimensão 4 fora do recorte brasileiro) vale para toda a série. A
ausência da dimensão 4 antes de 2017 não afeta o recorte, que já a exclui.

## Resumo das mudanças de leiaute

Apenas quatro transições em onze anos alteram colunas. As demais são estáveis.

| Transição | Tabela | Mudança |
|---|---|---|
| 2019 → 2020 | cursos | `CO_CINE_ROTULO` grafada como `CO_CINE_ROTULO2` |
| 2020 → 2021 | cursos | nome volta a `CO_CINE_ROTULO` |
| 2020 → 2021 | IES | entram `CO_LOCAL_OFERTA`, `NO_LOCAL_OFERTA`, `CO_PROJETO` |
| 2021 → 2022 | IES | as três colunas acima saem novamente |
| 2022 → 2023 | cursos | entram `IN_COMUNITARIA`, `IN_CONFESSIONAL` |
| 2022 → 2023 | IES | entram `TP_REDE`, `IN_COMUNITARIA`, `IN_CONFESSIONAL` |
| 2023 → 2024 | cursos | `QT_*_RVETNICO` sai; entram 24 colunas de reserva de vagas |

### `CO_CINE_ROTULO2` (2020)

O pacote de 2020 grafa a coluna com um dígito extra no fim. Em 2019 e em 2021
o nome é `CO_CINE_ROTULO`. Trata-se de erro de publicação isolado, não de
mudança de conceito: a união longitudinal deve normalizar o nome, e o
dicionário de 2020 confirma a intenção ao listar apenas `CO_CINE_ROTULO`.

### Colunas de local de oferta na tabela de IES (2021)

Somente em 2021 a tabela de IES traz `CO_LOCAL_OFERTA`, `NO_LOCAL_OFERTA` e
`CO_PROJETO` — nenhuma delas presente no dicionário daquele ano. Como aparecem
em uma única edição e sem documentação, não devem entrar na camada analítica
longitudinal; ficam preservadas apenas em `raw`.

### Categorização administrativa mais fina (2023)

`TP_REDE`, `IN_COMUNITARIA` e `IN_CONFESSIONAL` passam a existir em 2023.
Indicadores por natureza administrativa só são comparáveis em toda a série se
derivados de `TP_CATEGORIA_ADMINISTRATIVA`, presente desde 2014.

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

## Mudança de convenção para medidas inaplicáveis (2020)

Esta mudança não aparece na comparação de cabeçalhos: nenhuma coluna entra ou
sai. Ela só ficou visível ao tipar a série inteira em `staging`.

Cada dimensão carrega apenas parte das medidas. A dimensão 3 (oferta EAD
nacional) não descreve alunos, e a dimensão 2 (alunos EAD por localidade) não
descreve capacidade. O que mudou foi **como o arquivo representa a medida que
não se aplica**:

| Edições | Medida inaplicável à dimensão |
|---|---|
| 2014 a 2019 | campo vazio, que vira `NULL` na tipagem |
| 2020 a 2024 | valor literal `0` |

A transição é limpa e sem exceções. Em 2019, todas as 4.531 linhas da dimensão
3 têm ingressantes vazios e todas as 212.197 linhas da dimensão 2 têm vagas
vazias. Em 2020, nenhuma tem.

### Por que isso importa

O significado não mudou — ambos os padrões dizem "esta medida não se aplica a
esta dimensão". O risco é estatístico, não semântico:

- `SUM` não é afetado: nulo e zero contribuem igualmente nada;
- `AVG` e `COUNT` **são** afetados: até 2019 as linhas inaplicáveis ficam fora
  do denominador; de 2020 em diante entram como zero e derrubam a média;
- uma série de "vagas médias por oferta" calculada sem cuidado mostraria uma
  queda abrupta em 2020 que é puro artefato de publicação.

As métricas do MVP não são afetadas, porque a reconciliação já toma capacidade
apenas das dimensões 1 e 3 e alunos apenas das dimensões 1 e 2 — recortes em
que a medida sempre se aplica e nunca vem vazia. As asserções em
`sql/quality/042_assertions_staging_longitudinal.sql` verificam essas duas
garantias e também fixam o padrão observado, de modo que uma edição futura que
volte a mudar a convenção falhe de forma visível.

Regra geral para a série: qualquer indicador que use média, contagem ou desvio
padrão sobre uma medida deve filtrar explicitamente as dimensões em que essa
medida se aplica, em vez de confiar na ausência de nulos.

## Conclusão para a camada longitudinal

A série 2014–2024 é viável. As 200 colunas presentes em 2014 seguem presentes
em 2024, com uma única exceção real de conceito (`QT_*_RVETNICO`) e uma de
grafia (`CO_CINE_ROTULO2`). As medidas centrais do MVP — vagas, inscrições,
ingressantes, matrículas e concluintes — e as chaves `NU_ANO_CENSO`, `CO_IES`,
`CO_CURSO`, `CO_MUNICIPIO`, `TP_MODALIDADE_ENSINO` e `TP_DIMENSAO` existem em
todas as edições.

Regras que a união longitudinal deve seguir:

1. localizar tabelas por padrão de conteúdo, não por nome fixo;
2. unir por nome de coluna normalizado, nunca por posição ordinal;
3. normalizar `CO_CINE_ROTULO2` para `CO_CINE_ROTULO`;
4. restringir o mart longitudinal à interseção documentada de colunas;
5. manter fora do mart as colunas presentes em uma única edição;
6. tratar reserva de vagas por critério étnico/racial como série interrompida
   em 2024, não como continuidade;
7. obter rede de ensino do arquivo de cursos, onde `TP_REDE` existe desde
   2014, e não do arquivo de IES, onde só aparece em 2023;
8. filtrar dimensões antes de qualquer média, contagem ou desvio padrão, pela
   mudança de convenção de 2020 descrita acima.

## Próximas edições

Cada nova edição incorporada deve repetir esta comparação com a edição mais
recente já perfilada, registrando aqui apenas as mudanças reais de leiaute —
não a lista completa de colunas idênticas entre anos.
