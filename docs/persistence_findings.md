# Persistência e volatilidade — série 2014-2024

## O que este recorte responde

O MVP de 2024 mostrou ocupação baixa, sobretudo na EAD, mas um único ano não
distingue capacidade ociosa **persistente** de oscilação pontual. Com onze
edições carregadas, essa distinção passa a ser mensurável.

A unidade é a oferta: IES, curso e modalidade, acompanhada ao longo dos anos.

## Definições

- **Ocupação**: ingressantes divididos por vagas declaradas.
- **Ano ocioso**: ocupação abaixo de 0,25. O limiar fica abaixo da ocupação
  ponderada das duas modalidades em 2024 (32,8% presencial e 18,0% EAD), de
  modo a marcar conversão claramente fraca sem depender da modalidade.
- **Sequência ociosa atual**: anos ociosos consecutivos até a última
  observação da oferta.
- **Volatilidade da demanda**: coeficiente de variação dos ingressantes, ou
  seja, desvio padrão dividido pela média. É adimensional, o que permite
  comparar ofertas de escalas muito diferentes.

Ofertas com zero vagas declaradas ficam **fora** do cálculo. Elas não são
ociosas: são não mensuráveis, e tratá-las como ociosas inflaria a persistência.

## Achados

O recorte abaixo usa ofertas com pelo menos oito anos mensuráveis e sem
lacunas, para que persistência signifique algo.

| Medida | Presencial | EAD |
|---|---:|---:|
| Ofertas no painel longo | 24.094 | 1.504 |
| Proporção média de anos ociosos | 31,6% | 49,4% |
| Ofertas ociosas em **todos** os anos | 1.317 (5,5%) | 274 (18,2%) |
| Ofertas com cinco ou mais anos ociosos seguidos | 5.041 (20,9%) | 437 (29,1%) |
| Volatilidade média da demanda | 0,55 | 0,59 |

1. **A ociosidade da EAD é persistente, não conjuntural.** Uma oferta EAD do
   painel longo passa perto de metade dos anos abaixo de 25% de ocupação,
   contra menos de um terço no presencial. A proporção de ofertas ociosas em
   todos os anos observados é mais de três vezes maior.

2. **A capacidade ociosa persistente continua crescendo.** Entre as ofertas com
   cinco ou mais anos ociosos consecutivos, as vagas declaradas **aumentaram**
   entre o primeiro e o último ano observado: 18,8% no presencial e 75,1% na
   EAD. No último ano, essas ofertas concentram 1,54 milhão de vagas não
   convertidas no presencial e 3,62 milhões na EAD.

   Este é o padrão central da pergunta do projeto: a expansão não se concentra
   onde a conversão funciona. Ela também ocorre — e mais rápido — onde há
   histórico longo de não conversão.

3. **A volatilidade da demanda é alta e semelhante entre modalidades.** Um
   coeficiente de variação em torno de 0,55 significa que o desvio padrão dos
   ingressantes é mais da metade da média. A diferença entre modalidades é
   pequena, o que sugere que a ociosidade da EAD vem do nível da capacidade
   declarada, não de demanda mais instável.

## Limitações

- **Censura à esquerda e sobrevivência.** Apenas 12,3% das ofertas EAD têm oito
  anos ou mais, contra 50,2% do presencial: o ano inicial médio é 2020 na EAD e
  2016 no presencial. O painel longo da EAD é, portanto, um subconjunto de
  ofertas que sobreviveram. Se ofertas sobreviventes tendem a ser as mais
  saudáveis, a persistência real da ociosidade na EAD é provavelmente **maior**
  que a medida aqui, não menor.

- **Vaga declarada não é capacidade física.** Como já registrado nos achados de
  2024, a vaga pode representar teto regulatório ou comercial. O crescimento de
  vagas em ofertas ociosas indica declaração de capacidade, não necessariamente
  investimento em estrutura.

- **O limiar de 0,25 é uma convenção.** Ele está documentado e os componentes
  ficam expostos no mart para que outro limiar seja recalculado sem refazer a
  modelagem.

- **Estas medidas são descritivas e retrospectivas.** Elas usam a série
  inteira, inclusive anos posteriores a cada observação. Por isso não servem
  como atributos de um modelo preditivo, que exigirá recorte temporal sem
  informação futura.

- **Sem inferência causal.** O Censo é agregado e não sustenta afirmações sobre
  por que uma oferta não converte, nem conclusões sobre estudantes individuais.

- **Identidade da oferta ao longo do tempo.** O painel assume que a combinação
  de IES, curso e modalidade identifica a mesma oferta entre anos. Reformas
  cadastrais que alterem o código do curso apareceriam como oferta encerrada e
  oferta nova, não como continuidade.
