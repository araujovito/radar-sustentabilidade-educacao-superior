# Transição de modalidade e conclusão com defasagem

Análise da série 2014–2024 do Censo da Educação Superior. O relatório
reproduzível está em
[`reports/milestone3/metrics.json`](../reports/milestone3/metrics.json).

## Perguntas

1. A expansão da EAD substituiu diretamente a oferta presencial?
2. É possível melhorar a medida transversal de conclusão usando ingressantes
   de anos anteriores como denominador?

## Unidade comparável

Uma oferta presencial e uma oferta EAD geralmente têm códigos de curso
distintos. Por isso, a transição de modalidade não compara `CO_CURSO`. A unidade
é:

```text
ano × instituição × área CINE
```

Cada portfólio é classificado como presencial, EAD ou dual. A mudança anual
inclui entradas e saídas; a comparação de 2014 com 2024 usa somente pares
instituição–área presentes nos dois extremos e, portanto, é explicitamente um
painel de sobreviventes.

## A EAD ganhou dependência, mas substituição direta é minoritária

| Participação nacional da EAD | 2014 | 2019 | 2024 |
|---|---:|---:|---:|
| Vagas declaradas | 37,7% | 63,3% | 78,6% |
| Ingressantes | 23,4% | 43,8% | 66,8% |
| Matrículas | 17,1% | 28,5% | 50,7% |

A dependência da EAD cresce em todas as medidas, mas em velocidades diferentes:
a participação nas vagas permanece 11,8 pontos percentuais acima da
participação nos ingressantes em 2024. Escala de capacidade e conversão não são
sinônimos.

Os estados dos portfólios instituição–área mudaram assim:

| Estado | 2014 | 2024 |
|---|---:|---:|
| Somente presencial | 23.077 | 22.864 |
| Somente EAD | 482 | 6.577 |
| Dual | 820 | 4.111 |

No painel de 17.060 pares presentes tanto em 2014 quanto em 2024, 2.104
apresentam simultaneamente expansão de vagas EAD e retração presencial:
**12,3%**. A correlação entre as duas variações é **-0,08**, praticamente nula.

As transições de 2023 para 2024 reforçam a leitura. Houve 254 mudanças de
presencial para dual e apenas 14 de presencial diretamente para EAD. Outras
1.038 combinações instituição–área entraram já como EAD.

**Conclusão:** a EAD domina a expansão e aumenta a dependência do sistema, mas
os dados agregados não sustentam a narrativa de uma substituição direta e
generalizada do presencial. O padrão predominante é criação de portfólio EAD e
dualização, com substituição observável em uma parcela minoritária dos
portfólios sobreviventes.

Isso é descrição, não efeito causal. A análise não identifica se uma vaga EAD
provocou o recuo de uma vaga presencial.

## Eficiência de conclusão com defasagem

A medida candidata compara concluintes no ano `t` com ingressantes da mesma
oferta em `t-3`, `t-4` e `t-5`. Entram apenas ofertas presentes nos dois anos e
com pelo menos 20 ingressantes no ano-base.

Resultados de 2024:

| Modalidade | Defasagem | Cobertura | Razão agregada | Mediana | Acima de 100% |
|---|---:|---:|---:|---:|---:|
| Presencial | 3 anos | 55,3% | 47,0% | 44,1% | 5,8% |
| Presencial | 4 anos | 61,9% | 40,3% | 36,7% | 3,9% |
| Presencial | 5 anos | 64,9% | 35,8% | 31,6% | 3,0% |
| EAD | 3 anos | 41,6% | 23,1% | 21,7% | 3,3% |
| EAD | 4 anos | 34,2% | 26,7% | 24,6% | 6,2% |
| EAD | 5 anos | 25,9% | 31,2% | 26,7% | 7,2% |

A defasagem de quatro anos é a referência central mais interpretável, mas não
é universal: cursos têm durações diferentes e a EAD cresceu rapidamente. Esse
crescimento faz a cobertura da EAD cair de 41,6% no atraso de três anos para
25,9% no de cinco anos e altera o próprio valor da razão.

### Veredito de validação

A razão defasada é superior à intensidade transversal
`concluintes / matrículas do mesmo ano` para monitorar o sistema, porque
aproxima temporalmente entrada e conclusão. Ela é válida como **proxy agregada
com análise de sensibilidade entre três e cinco anos**.

Ela não é uma taxa de conclusão de coorte e não deve ser usada isoladamente
para ranquear cursos. O Censo agregado não permite rastrear:

- se o concluinte ingressou naquela oferta no ano-base;
- transferências, reingressos e mudanças cadastrais;
- a duração específica de cada curso;
- coortes sobrepostas.

Razões acima de 100% são preservadas e quantificadas como diagnóstico de
mistura de coortes; truncá-las esconderia o principal limite da medida.

## Reprodução

Após aplicar `sql/analytics/037_modality_completion.sql` ao banco longitudinal:

```bash
radar build-milestone3-report
```

O comando grava as definições, limitações e resultados legíveis por máquina em
`reports/milestone3/metrics.json`.
