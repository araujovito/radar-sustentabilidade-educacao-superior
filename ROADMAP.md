# Roadmap

## Marco 0 — Fundação

- [x] Criar o repositório público.
- [x] Definir pergunta central e princípios analíticos.
- [x] Criar estrutura inicial de Python e SQL.
- [x] Configurar PostgreSQL para desenvolvimento local.
- [x] Instalar dependências e executar os testes no ambiente local.

## Marco 1 — Inventário e aquisição

- [x] Selecionar o recorte temporal inicial.
- [x] Registrar os arquivos oficiais, URLs e localização dos dicionários.
- [x] Implementar download com retomada, checksum e idempotência.
- [x] Criar relatório de qualidade por arquivo e ano.
- [x] Documentar mudanças de leiaute entre edições.

## Marco 2 — Banco analítico

- [x] Gerar a camada `raw` a partir do leiaute oficial.
- [x] Padronizar chaves, tipos, categorias e valores ausentes em `staging`.
- [x] Criar a visão analítica por instituição, curso e modalidade.
- [x] Reconciliar oferta e alunos nas dimensões específicas da EAD.
- [x] Implementar testes de unicidade, integridade e reconciliação.
- [x] Executar a carga completa no PostgreSQL local.
- [x] Criar a camada `raw` longitudinal de 2014 a 2024.
- [x] Padronizar tipos e chaves da série em `staging`.

## Marco 3 — Métricas e hipóteses

- [x] Definir taxa de ocupação com denominadores comparáveis.
- [ ] Construir indicador de capacidade ociosa persistente.
- [ ] Medir volatilidade da demanda e persistência do crescimento.
- [x] Calcular concentração do portfólio por instituição.
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
