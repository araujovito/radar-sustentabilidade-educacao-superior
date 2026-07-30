# Metodologia

## Unidade de análise

O mart principal usa:

```text
ano × instituição × curso × modalidade
```

Vagas EAD vêm da dimensão nacional e estudantes da dimensão municipal; as duas
fontes são reconciliadas pelas chaves da oferta. A dimensão exterior não
participa do recorte.

Comparações entre modalidades usam `ano × instituição × área CINE`, porque
códigos de curso identificam ofertas específicas e não são equivalentes entre
presencial e EAD.

## Famílias de métricas

1. **Capacidade e conversão:** vagas, ingressantes e ocupação.
2. **Fluxo:** permanência, desistência e conclusão.
3. **Portfólio:** concentração, diversificação e dependência de modalidade.
4. **Dinâmica:** crescimento, volatilidade e persistência.
5. **Risco:** probabilidade de deterioração futura definida por evento observável.

As métricas de conclusão comparam defasagens de três, quatro e cinco anos,
exigem pelo menos 20 ingressantes no denominador e mantêm razões acima de 100%
como diagnóstico de mistura de coortes.

## Validação preditiva

Os conjuntos de treino e teste respeitarão o tempo. Atributos do ano `t` serão
usados apenas para prever um evento posterior. Métricas calculadas com janelas
móveis serão truncadas na data de referência para impedir vazamento.

Na implementação final, treino cobre 2016–2020 e teste cobre 2021–2022. A
ausência de vazamento é verificada recomputando atributos sobre uma série
truncada. A avaliação compara regressão logística, gradient boosting e um
baseline que ordena apenas por tamanho.

## Limitações

Associações observacionais não serão apresentadas como efeitos causais. Mudanças
de definição, cobertura ou leiaute serão registradas e tratadas antes da
comparação longitudinal.

Vaga declarada pode ser teto regulatório ou comercial; conclusão defasada não é
taxa de coorte; desaparecimento de uma oferta pode representar encerramento ou
mudança cadastral. O alerta opera por ranking, não por limiar de probabilidade.
