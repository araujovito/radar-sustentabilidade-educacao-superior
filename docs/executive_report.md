# Relatório executivo

Radar de Sustentabilidade da Educação Superior — série 2014 a 2024 dos
microdados do Censo da Educação Superior do Inep.

## A resposta em um parágrafo

A oferta de graduação no Brasil quase triplicou a capacidade declarada em onze
anos — de 8,1 para 23,7 milhões de vagas, um fator de 2,9 — enquanto os
ingressantes cresceram 61%, de 3,1 para 5,0 milhões. A ocupação caiu de 38,5%
para 21,2%. Isso não é um efeito
de um ano ruim: entre as ofertas com histórico longo, quase metade dos anos da
EAD ficam abaixo de 25% de ocupação, e as ofertas com cinco anos ou mais de
ociosidade consecutiva **aumentaram** suas vagas declaradas no período — 19% no
presencial e 75% na EAD. A expansão não se concentra onde a conversão funciona.

## Onde está o problema

### A escala está na EAD, a conversão não acompanha

Em 2024, a EAD concentra 78,5% das vagas declaradas, 66,8% dos ingressantes e
50,7% das matrículas. A ocupação ponderada é de 18,0% na EAD contra 32,8% no
presencial.

O gargalo não é apenas falta de procura, mas a comparação exige cautela: o
presencial registra 1,71 inscrição por vaga e a EAD, 0,38. Como as regras de
inscrição diferem entre modalidades, isso funciona como sinal de diagnóstico,
não como prova.

### A ociosidade é persistente, não conjuntural

Entre ofertas com pelo menos oito anos observados e sem lacunas:

| Medida | Presencial | EAD |
|---|---:|---:|
| Proporção média de anos com ocupação abaixo de 25% | 31,6% | 49,4% |
| Ofertas ociosas em **todos** os anos observados | 5,5% | 18,2% |
| Ofertas com cinco anos ou mais de ociosidade seguida | 20,9% | 29,1% |
| Volatilidade média da demanda | 0,55 | 0,59 |

A volatilidade é praticamente igual entre modalidades. Isso é informativo: a
ociosidade da EAD vem do **nível da capacidade declarada**, não de demanda mais
instável.

### A capacidade ociosa cresce

Entre as ofertas com cinco anos ou mais de ociosidade consecutiva, as vagas
declaradas subiram 18,8% no presencial e 75,1% na EAD entre a primeira e a
última observação. No último ano, essas ofertas concentram 1,54 milhão de vagas
não convertidas no presencial e 3,62 milhões na EAD.

### A expansão da EAD não equivale a substituição direta

A participação da EAD passou de 37,7% para 78,6% das vagas e de 17,1% para
50,7% das matrículas entre 2014 e 2024. Entretanto, entre 17.060 combinações
IES–área CINE presentes nos dois extremos, somente 12,3% combinam expansão EAD
e retração presencial. A correlação entre essas variações é -0,08.

O movimento dominante é criação de portfólios EAD e dualização, não troca
direta: de 2023 para 2024, 254 portfólios passaram de presencial para dual e
apenas 14 passaram diretamente de presencial para EAD.

### Conclusão defasada melhora o denominador, mas não cria coortes

Com quatro anos de defasagem, concluintes de 2024 representam 40,3% dos
ingressantes de 2020 nas ofertas presenciais elegíveis e 26,7% nas EAD. A
cobertura é 61,9% e 34,2%, respectivamente. Variar a defasagem entre três e
cinco anos altera materialmente cobertura e resultado, sobretudo na EAD.

A medida é usada como proxy agregada com análise de sensibilidade. Ela não
rastreia indivíduos e não deve ranquear cursos isoladamente.

## O que torna isso acionável

O fenômeno é extremamente concentrado. Das 2.526 instituições com capacidade
declarada em 2024, a distribuição das 18,6 milhões de vagas não convertidas é:

| Instituições (ordenadas por vagas ociosas) | Participação acumulada |
|---|---:|
| 1 | 21,6% |
| 5 | 38,4% |
| 10 | 48,2% |
| 20 | 59,8% |
| 50 | 72,8% |

Uma única instituição responde por mais de um quinto de toda a capacidade não
convertida do país. Cinquenta instituições respondem por quase três quartos.
**Auditoria não precisa ser censitária para cobrir a maior parte do fenômeno.**

Em 2024, 4.886 ofertas presenciais e 1.830 ofertas EAD ativas acumulam cinco
anos ou mais de ociosidade consecutiva. Essa é uma lista de trabalho de tamanho
administrável.

## O sistema de alerta

Modelo que estima, para cada oferta, a probabilidade de deterioração em dois
anos — matrículas caindo abaixo da metade, ou saída do Censo.

Treinado em 2016-2020 e avaliado em 2021-2022, anos nunca vistos:

| Modelo | AUC | Precisão nas 100 primeiras |
|---|---:|---:|
| Ordenar apenas por tamanho | 0,719 | 44% |
| Regressão logística | 0,813 | 84% |
| Gradient boosting | 0,848 | 95% |

Com taxa base de 16,7%, acertar 95% das cem ofertas de maior risco é cerca de
5,7 vezes o acerto aleatório.

**Como operar:** por ranking, não por limiar de probabilidade. O modelo é
sistematicamente superconfiante fora do tempo — em decis intermediários prevê
quase o dobro da frequência observada. A calibração reduziu o erro em 25%, mas
não o eliminou, porque a taxa base cai de forma contínua ao longo da série e
calibrar em um ano não antecipa a queda dos seguintes. A ordenação é confiável;
o número absoluto não é.

**Ressalva operacional:** as ofertas de maior risco concentram-se em poucas
instituições e repetem os mesmos cursos em anos diferentes. Uma lista de
auditoria precisa de regra de diversificação, ou uma única instituição consome
toda a capacidade de análise.

## Confiabilidade do trabalho

Decisões metodológicas que sustentam os números acima:

- **Reconciliação das dimensões da EAD.** O arquivo do Censo separa capacidade
  (dimensão 3, nacional) de alunos (dimensão 2, por município). Somar as duas
  produziria dupla contagem. A oferta no exterior (dimensão 4) fica fora do
  recorte brasileiro.
- **Comparabilidade entre anos verificada, não presumida.** Em onze edições,
  apenas quatro transições alteram colunas. Todas estão documentadas, incluindo
  uma mudança de convenção em 2020 — medidas inaplicáveis a uma dimensão passam
  de campo vazio para zero — que não aparece na comparação de cabeçalhos e
  distorceria qualquer média calculada sem filtrar dimensão.
- **Ausência de vazamento temporal provada por recomputação.** Os atributos do
  modelo são reconstruídos sobre a série truncada e comparados com os valores
  produzidos com a série completa. Divergência falharia a verificação.
- **Separação cronológica.** Uma divisão aleatória colocaria a mesma oferta em
  treino e teste em anos vizinhos, e o modelo aprenderia a reconhecer a oferta
  em vez de antecipar deterioração.
- **Ablação de escala.** Como o rótulo é uma queda pela metade, estoques
  grandes têm dificuldade aritmética de cair. Medir o desempenho de ordenar
  apenas por tamanho mostra quanto do resultado é essa mecânica.
- **Verificação automatizada.** Cada push executa estilo, testes e a aplicação
  completa do esquema SQL contra um fixture construído para exercitar
  reconciliação, normalização e rotulagem.

## Limites que mudam a leitura

- **Vaga declarada não é capacidade física.** Pode representar teto regulatório
  ou comercial. O crescimento de vagas em ofertas ociosas indica declaração de
  capacidade, não necessariamente investimento em estrutura.
- **Sobrevivência no painel da EAD.** Apenas 12,3% das ofertas EAD têm oito
  anos ou mais, contra 50,2% do presencial. O painel longo da EAD é um
  subconjunto de sobreviventes. Se sobreviventes tendem a ser mais saudáveis, a
  persistência real da ociosidade na EAD é provavelmente **maior** que a medida
  aqui.
- **Sem inferência causal.** O Censo é agregado. Nada aqui explica por que uma
  oferta não converte, nem sustenta conclusões sobre estudantes individuais.
- **Desaparecimento é ambíguo.** Sair do Censo pode ser encerramento ou
  mudança de código cadastral. Responde por 30% a 42% dos eventos e fica
  marcado separadamente para que o desempenho possa ser medido sem esses casos.
- **O modelo prevê matrículas, não solvência.** Não mede saúde financeira,
  qualidade de ensino nem risco regulatório.
- **Intensidade de conclusão não é taxa de sucesso.** Numerador e denominador
  não pertencem à mesma coorte. No modelo, o valor máximo identifica ofertas em
  encerramento — que formam a turma inteira sem repor ingressantes — e não
  desempenho acadêmico.

## Detalhamento

- [Achados de qualidade de 2024](2024_quality_findings.md)
- [Achados analíticos do MVP 2024](mvp_2024_findings.md)
- [Mudanças de leiaute entre edições](layout_changes.md)
- [Persistência e volatilidade](persistence_findings.md)
- [Transição de modalidade e conclusão defasada](modality_completion_findings.md)
- [Sistema de alerta](alerting_findings.md)
- [Modelo SQL](sql_model.md)
