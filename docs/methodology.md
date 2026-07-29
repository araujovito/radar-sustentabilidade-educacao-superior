# Metodologia inicial

## Unidade de análise

A unidade principal candidata é a combinação de instituição, curso, local de
oferta, modalidade e ano. A granularidade definitiva dependerá da estabilidade
das chaves e da comparabilidade dos leiautes do Censo da Educação Superior.

## Famílias de métricas

1. **Capacidade e conversão:** vagas, ingressantes e ocupação.
2. **Fluxo:** permanência, desistência e conclusão.
3. **Portfólio:** concentração, diversificação e dependência de modalidade.
4. **Dinâmica:** crescimento, volatilidade e persistência.
5. **Risco:** probabilidade de deterioração futura definida por evento observável.

## Validação preditiva

Os conjuntos de treino e teste respeitarão o tempo. Atributos do ano `t` serão
usados apenas para prever um evento posterior. Métricas calculadas com janelas
móveis serão truncadas na data de referência para impedir vazamento.

## Limitações

Associações observacionais não serão apresentadas como efeitos causais. Mudanças
de definição, cobertura ou leiaute serão registradas e tratadas antes da
comparação longitudinal.
