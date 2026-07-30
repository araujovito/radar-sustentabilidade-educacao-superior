# Sistema de alerta de deterioração

## Evento previsto

Uma oferta observada no ano t deteriora se, em t+2, as matrículas caem abaixo
de metade do nível de t, ou se a oferta deixa de constar no Censo.

Escolhas registradas:

- **Matrículas e não ingressantes.** Ingressantes são fluxo, com coeficiente de
  variação em torno de 0,55 na série. Uma queda de um ano em ingressantes é
  frequentemente ruído. Matrículas são estoque e caem pela metade só com
  deterioração real.
- **Dois anos.** Dá tempo de o efeito aparecer no estoque e ainda é horizonte
  em que uma decisão institucional é possível.
- **Desaparecimento conta como evento.** Do ponto de vista de decisão, sair do
  Censo é deixar de operar. A ambiguidade é real — pode ser encerramento ou
  mudança cadastral — e por isso fica marcada em `disappeared_from_census`. O
  desaparecimento responde por 30% a 42% dos eventos, dependendo do ano.
- **Escala mínima de 20 matrículas.** Abaixo disso, poucos alunos cruzam o
  limiar de metade do estoque e o rótulo mediria ruído.

## Ausência de vazamento temporal

Os atributos vêm de `analytics.offer_features`, onde toda janela acumulada usa
`ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` sobre o ano ascendente. As
métricas de `analytics.course_persistence` estão **proibidas** aqui: elas
resumem a série inteira, inclusive anos posteriores a cada observação.

A propriedade não é verificada por leitura do SQL. Uma asserção em
`sql/quality/044_assertions_features.sql` recomputa os atributos acumulados
usando apenas os anos até 2019 e exige igualdade com o que a view produz para
`reference_year = 2019` tendo toda a série disponível. Se qualquer janela
olhasse adiante, os valores divergiriam.

Defasagens usam aritmética de ano, não `LAG`: a série tem lacunas e `LAG`
compararia anos não adjacentes.

## Separação e desempenho

Separação cronológica, não aleatória: uma divisão aleatória colocaria a mesma
oferta em treino e teste em anos vizinhos, e o modelo aprenderia a reconhecer a
oferta em vez de antecipar deterioração.

- treino: 2016 a 2020 — 161.970 linhas, taxa de evento 17,7%
- teste: 2021 a 2022 — 69.255 linhas, taxa de evento 16,7%

| Modelo | AUC | Precisão média | Brier | p@100 | p@1000 |
|---|---:|---:|---:|---:|---:|
| Apenas escala | 0,719 | 0,324 | — | 0,440 | 0,443 |
| Regressão logística | 0,813 | 0,538 | 0,113 | 0,840 | 0,829 |
| Gradient boosting | 0,848 | 0,607 | 0,101 | 0,950 | 0,905 |

A taxa base no teste é 16,7%. A precisão nas 100 ofertas de maior risco
previsto é 84% na regressão logística e 95% no gradient boosting — cinco a seis
vezes a taxa base.

## O quanto disso é apenas tamanho

A ablação "apenas escala" ordena as ofertas pelo inverso do estoque de
matrículas, sem treinar nada. Ela existe porque o rótulo é uma queda de metade
do estoque, e estoques grandes têm dificuldade aritmética de cair pela metade —
parte do desempenho pode ser essa mecânica, não sinal de sustentabilidade.

O resultado é honesto nos dois sentidos: tamanho sozinho já alcança AUC 0,719,
o que é bastante. Mas a precisão nas 100 primeiras cai de 84% para 44%, e a
precisão média cai de 0,538 para 0,324. Ou seja, o histórico de ocupação, a
volatilidade e o contexto institucional acrescentam sinal real, sobretudo no
topo do ranking, que é onde o sistema seria usado.

O maior coeficiente da regressão logística continua sendo o de matrículas
(-1,55), o que confirma que escala é o eixo dominante. Qualquer leitura do
modelo deve começar por aí.

## Calibração: melhora, mas não resolve

O modelo é sistematicamente **superconfiante** fora do tempo. Nos decis
intermediários, prevê muito mais deterioração do que a observada.

A calibração isotônica foi ajustada em um recorte reservado — o modelo base usa
2016 a 2019 e a calibração usa somente 2020, ano posterior ao ajuste e anterior
ao teste. Calibrar no teste inflaria o resultado; calibrar nos anos do próprio
ajuste não corrigiria deriva alguma.

Comparando o mesmo modelo base, com e sem calibração, no teste de 2021-2022:

| Decil | Base: previsto | Base: observado | Calibrada: previsto | Calibrada: observado |
|---:|---:|---:|---:|---:|
| 4 | 0,153 | 0,073 | 0,110 | 0,068 |
| 5 | 0,222 | 0,094 | 0,152 | 0,089 |
| 7 | 0,410 | 0,215 | 0,375 | 0,203 |
| 9 | 0,782 | 0,624 | 0,701 | 0,606 |

O erro médio de calibração cai de 0,107 para 0,081, uma redução de 25%. Mas a
superconfiança permanece: no decil 5, a probabilidade prevista ainda é quase o
dobro da frequência observada.

A causa provável é deriva monotônica da taxa base. Os anos de treino de maior
peso ficam em torno de 20% de eventos, 2021 tem 18,2% e 2022 tem 15,2%.
Calibrar em 2020 não antecipa uma queda que continua depois.

**Consequência prática:** o ranking é confiável, as probabilidades absolutas
não. O sistema deve ser operado por `precision@k` — auditar as k ofertas de
maior risco — e não por limiar de probabilidade.

Nota técnica: a calibração isotônica levou o decil mais baixo a prever quase
zero (0,0001) contra 0,063 observado. É um artefato conhecido do método nas
caudas e outro motivo para não ler as probabilidades como literais.

## Interpretação dos coeficientes

Os contínuos estão padronizados, então o coeficiente é o efeito de um desvio
padrão sobre o log-odds. Os categóricos são indicadores comparados à categoria
de referência omitida.

| Atributo | Coeficiente |
|---|---:|
| Matrículas | -1,55 |
| Rede privada | +0,73 |
| Categoria administrativa 3 (pública municipal) | +0,70 |
| Intensidade de conclusão | +0,63 |
| Categoria administrativa 4 (privada com fins lucrativos) | +0,60 |
| Volatilidade da demanda acumulada | +0,56 |
| Modalidade EAD | -0,28 |

`TP_CATEGORIA_ADMINISTRATIVA` assume os códigos 1, 2, 3, 4, 5 e 7, que não têm
ordem. Tratá-los como número faria o modelo supor um efeito monotônico do
código, sem significado. Por isso entram como indicadores.

Nenhum coeficiente autoriza leitura causal: os atributos são correlacionados
entre si, e o Censo é agregado. A intensidade de conclusão com sinal positivo,
por exemplo, provavelmente reflete ofertas em encerramento, que concluem turmas
sem repor ingressantes — não que concluir mais cause deterioração.

## Explicações por previsão

Na regressão logística a decomposição é **exata**, não aproximada: o log-odds é
a soma do intercepto com o produto de cada coeficiente pelo valor padronizado
do atributo. Isso dispensa métodos de atribuição aproximada e permite auditar
cada alerta. Um teste verifica a identidade numericamente.

Entre as 20 ofertas de maior risco previsto no teste, 14 deterioraram de fato.
A explicação delas segue um padrão único e legível — exemplo real:

```text
IES 1893, curso 51149, presencial, 2022
probabilidade 0,997   observado: deteriorou
log-odds 5,71 = intercepto -2,83 + contribuições

  graduation_intensity          valor +5,51 sd   contribuição +3,48
  demand_volatility_to_date     valor +4,28 sd   contribuição +2,38
  rede privada                                   contribuição +0,73
  privada com fins lucrativos                    contribuição +0,60
  current_low_occupancy_streak   valor +5,02 sd  contribuição +0,45
```

O atributo dominante é a intensidade de conclusão. Ela é limitada ao intervalo
de 0 a 1, com mediana 0,134 e percentil 99 em 0,765. Um valor igual a 1
significa que a oferta formou **toda** a turma matriculada sem reposição de
ingressantes — estado terminal, não desempenho. É por isso que aparece a mais
de cinco desvios padrão e domina a explicação.

Isso confirma a hipótese registrada na seção de coeficientes: a intensidade de
conclusão com sinal positivo identifica ofertas em encerramento, não sucesso
acadêmico que causaria deterioração.

**Ressalva operacional:** as 20 primeiras concentram-se em poucas instituições
e repetem os mesmos cursos em anos diferentes. Uma lista de auditoria precisaria
de regra de diversificação, ou uma única instituição consumiria toda a
capacidade de análise.

## Estabilidade

O modelo foi retreinado em janelas deslizantes de três anos dentro do treino,
sempre avaliado no mesmo teste de 2021-2022.

| Janela de treino | AUC | Precisão média | p@1000 |
|---|---:|---:|---:|
| 2016-2018 | 0,806 | 0,523 | 0,802 |
| 2017-2019 | 0,810 | 0,534 | 0,834 |
| 2018-2020 | 0,816 | 0,544 | 0,841 |

O desempenho é estável e melhora levemente com janelas mais recentes, o que é
esperado: elas estão mais próximas do período de teste.

A sobreposição das 1.000 ofertas de maior risco entre janelas consecutivas,
medida por índice de Jaccard, é 0,85 e 0,78. O modelo aponta substancialmente
as mesmas ofertas independentemente de quais três anos o treinaram.

### Instabilidade de coeficientes: onde ela é e onde não é

Quatro atributos trocam de sinal entre janelas. A leitura ingênua seria
concluir que o modelo é frágil. A magnitude mostra o contrário:

| Trocam de sinal | maior valor absoluto |
|---|---:|
| Categoria administrativa 2 (pública estadual) | 0,220 |
| `years_observed_to_date` | 0,170 |
| `occupancy_rate` | 0,133 |
| `institution_offer_count` | 0,125 |

| Sinal estável | menor valor absoluto |
|---|---:|
| `enrollments` | 1,265 |
| `graduation_intensity` | 0,584 |
| `demand_volatility_to_date` | 0,548 |
| Rede privada | 0,484 |

A separação é limpa: tudo que troca de sinal tem coeficiente **menor que
0,22**, e tudo que é estável tem coeficiente **maior que 0,46**. Os atributos
instáveis oscilam em torno de zero porque carregam pouco sinal próprio, não
porque o modelo seja instável.

A causa é colinearidade. Seis atributos medem ocupação — nível, defasagem,
variação, média acumulada, proporção de anos ociosos e sequência ociosa. Eles
dividem um sinal compartilhado, e a atribuição entre eles é arbitrária mesmo
quando o conjunto é informativo.

**Consequência:** as contribuições individuais de atributos de ocupação em uma
explicação não devem ser lidas como "o peso da ocupação". A soma do bloco é
interpretável; a divisão dentro dele, não. Os atributos de coeficiente grande
e estável — escala, intensidade de conclusão, volatilidade e natureza
administrativa — sustentam leitura individual.

## Limitações

- O gradient boosting sobreajusta mais: AUC 0,894 no treino contra 0,848 no
  teste, enquanto a regressão logística vai de 0,818 para 0,813. A regressão
  é notavelmente estável e permanece como referência.
- O rótulo de 2020 usa o horizonte de 2022, que é também ano de referência do
  teste. Não há vazamento de atributos — o modelo nunca vê 2021 ou 2022 ao
  treinar — mas existe sobreposição de calendário entre horizontes, registrada
  para leitura honesta das métricas.
- A identidade da oferta ao longo do tempo depende de IES, curso e modalidade.
  Reformas cadastrais que alterem o código do curso aparecem como oferta
  encerrada, e portanto como evento.
- O modelo prevê deterioração de matrículas, não insustentabilidade
  financeira, qualidade de ensino ou risco regulatório.
