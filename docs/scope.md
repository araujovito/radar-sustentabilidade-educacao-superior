# Recorte analítico inicial

## Decisão

O MVP começa com o Censo da Educação Superior de 2024. A primeira entrega será
transversal: ela deverá provar que as chaves, os denominadores e as métricas são
reproduzíveis antes da expansão para uma série histórica.

Após o controle de qualidade de 2024, o projeto incorporará gradualmente as
edições de 2014 a 2024. Essa ordem reduz o risco de misturar mudanças de leiaute
com mudanças reais do sistema educacional.

## Pergunta de decisão

> Em quais combinações de instituição, curso, local de oferta e modalidade a
> capacidade declarada é convertida em ingressantes, matrículas e concluintes,
> e onde aparecem sinais de ociosidade ou fragilidade?

O MVP não tentará explicar causalmente por que uma oferta é sustentável. Ele
construirá uma base confiável para descrição, segmentação e, posteriormente,
previsão.

## População

- cursos de graduação presentes nos microdados oficiais do Censo da Educação
  Superior de 2024;
- instituições públicas e privadas;
- modalidades presencial e a distância;
- unidades geográficas brasileiras disponibilizadas no arquivo oficial.

Registros fora desse universo só serão incluídos se o dicionário de dados
mostrar que são necessários para reconciliar totais oficiais.

## Grão pretendido

```text
ano × instituição × curso × local de oferta × modalidade
```

Esse é o grão analítico pretendido, não uma chave presumida. A combinação será
testada contra duplicidades e contra a documentação do Inep. Caso a fonte tenha
um nível mais detalhado, o dado será preservado na camada `raw` e agregado
explicitamente em uma camada posterior.

## Dimensões iniciais

- instituição e categoria administrativa;
- curso e classificação Cine Brasil;
- modalidade de ensino;
- município e unidade da Federação;
- ano de referência.

## Medidas candidatas

- vagas oferecidas;
- ingressantes;
- matrículas;
- concluintes;
- inscrições ou candidatos, quando comparáveis;
- medidas auxiliares necessárias para reconciliar os totais publicados.

Os nomes definitivos das colunas serão estabelecidos apenas depois da leitura
do dicionário distribuído no pacote oficial.

## Fora do escopo do MVP

- inferência causal;
- acompanhamento individual de estudantes;
- pós-graduação stricto sensu;
- associação direta com salários ou ocupações;
- criação de um índice composto de risco antes da validação das métricas-base;
- comparação longitudinal antes do mapeamento das mudanças de leiaute.

## Critérios para avançar à série histórica

1. Arquivo de 2024 baixado com checksum e manifesto.
2. Conteúdo do ZIP inventariado sem extração insegura.
3. Dicionário de dados localizado e versionado por hash.
4. Tipos, chaves e categorias perfilados.
5. Totais principais reconciliados com publicação oficial.
6. Denominadores de vagas, ingressantes e concluintes documentados.
