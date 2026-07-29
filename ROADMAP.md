# Roadmap

## Marco 0 — Fundação

- [x] Criar o repositório público.
- [x] Definir pergunta central e princípios analíticos.
- [x] Criar estrutura inicial de Python e SQL.
- [x] Configurar PostgreSQL para desenvolvimento local.
- [ ] Instalar dependências e executar os testes no ambiente local.

## Marco 1 — Inventário e aquisição

- [ ] Selecionar o recorte temporal inicial.
- [ ] Registrar os arquivos oficiais, URLs e dicionários de dados.
- [ ] Implementar download com retomada, checksum e idempotência.
- [ ] Criar relatório de qualidade por arquivo e ano.
- [ ] Documentar mudanças de leiaute entre edições.

## Marco 2 — Banco analítico

- [ ] Carregar uma amostra na camada `raw`.
- [ ] Padronizar chaves, tipos, categorias e valores ausentes em `staging`.
- [ ] Criar dimensões de tempo, instituição, curso e localidade.
- [ ] Criar fatos de oferta, matrícula e fluxo.
- [ ] Implementar testes de unicidade, integridade e reconciliação.

## Marco 3 — Métricas e hipóteses

- [ ] Definir taxa de ocupação com denominadores comparáveis.
- [ ] Construir indicador de capacidade ociosa persistente.
- [ ] Medir volatilidade da demanda e persistência do crescimento.
- [ ] Calcular concentração do portfólio por instituição.
- [ ] Estudar transição e dependência entre presencial e EAD.
- [ ] Validar uma medida de eficiência de conclusão com defasagem.

## Marco 4 — Sistema de alerta

- [ ] Definir evento de deterioração em horizonte de dois anos.
- [ ] Criar tabela de atributos sem vazamento temporal.
- [ ] Estabelecer modelo de referência interpretável.
- [ ] Comparar modelos e calibrar probabilidades.
- [ ] Avaliar desempenho fora do tempo e `precision@k`.
- [ ] Produzir explicações por previsão e análise de estabilidade.

## Marco 5 — Produto de portfólio

- [ ] Criar painel orientado a decisões.
- [ ] Publicar relatório executivo com achados e limitações.
- [ ] Automatizar testes e verificações no GitHub Actions.
- [ ] Preparar demonstração reproduzível e documentação final.
