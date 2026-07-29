# MVP analítico — Censo da Educação Superior 2024

## O que este recorte responde

Este MVP mede como a capacidade declarada em 2024 se converte em ingressantes,
matrículas e concluintes. A unidade é a combinação de ano, IES, curso e
modalidade. O recorte inclui apenas graduação no Brasil.

O principal cuidado metodológico é a EAD: vagas e inscrições vêm da dimensão 3
do arquivo, enquanto ingressantes, matrículas e concluintes são somados a partir
da dimensão 2. Somar essas dimensões diretamente produziria dupla contagem.

## Achados

1. **A escala de vagas EAD é muito maior que sua conversão.** A modalidade
   concentra 78,5% das 23,7 milhões de vagas declaradas, mas 66,8% dos
   ingressantes e 50,7% das matrículas. A ocupação ponderada é 18,0%, contra
   32,8% no presencial.

2. **O gargalo não pode ser interpretado apenas como falta de procura.** O
   presencial registra 1,71 inscrição por vaga e a EAD, 0,38. Como as regras de
   inscrição e oferta diferem entre modalidades, a comparação funciona como
   sinal de diagnóstico, não como prova causal.

3. **Há caudas extremas de capacidade não convertida.** Algumas combinações de
   IES e curso declaram dezenas de milhares de vagas com ocupação abaixo de 1%.
   Essas observações são úteis para auditoria e segmentação, mas a vaga declarada
   pode representar teto regulatório/comercial, e não capacidade física
   imediatamente disponível.

4. **Concentração de portfólio revela exposição estratégica.** O HHI das
   matrículas identifica instituições cujo volume depende fortemente de poucos
   cursos. O ranking exige pelo menos cinco cursos e mil matrículas para evitar
   que instituições muito pequenas dominem o resultado.

5. **A intensidade de conclusão é descritiva, não uma taxa de sucesso.** A razão
   entre concluintes e matrículas do mesmo ano é 14,5% no presencial e 11,7% na
   EAD. Como numerador e denominador não pertencem à mesma coorte, ela não mede
   probabilidade individual de conclusão.

## Por que o resultado é mais útil que um ranking simples

O diagnóstico separa três mecanismos: escala de oferta, atração de candidatos e
conversão em ingressantes. Também adiciona a concentração do portfólio, que
mede vulnerabilidade estratégica diferente de baixa ocupação. Assim, uma IES
pode ter ocupação aceitável e ainda apresentar risco por depender de poucos
cursos — ou o inverso.

## Limitações

- Um único ano não permite chamar capacidade ociosa de persistente.
- O Censo é agregado; não sustenta inferência sobre estudantes individuais.
- Comparações de vagas e inscrições entre modalidades exigem cautela
  institucional e regulatória.
- A razão de conclusão só se tornará uma medida de fluxo quando houver coortes
  e defasagens adequadas.

O próximo passo temporal é incorporar anos anteriores e testar persistência,
volatilidade e transições de estado sem usar informação futura.
