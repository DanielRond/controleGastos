# Specs

Contrato do que o sistema faz, por **capacidade** (uma fatia coesa de comportamento, não uma camada técnica). O spec permanece depois de pronto: o código e os testes respondem a ele, e divergência é bug.

Lido da mesma forma pelo Kiro, pelo Claude Code e por pessoas. Idioma: pt-BR (o do projeto e do usuário), com IDs e palavras-chave estáveis para agentes.

| Capacidade | Código | Status | O que cobre |
|---|---|---|---|
| [lancamentos](lancamentos/spec.md) | LAN | vigente | JSON vira `LivroCaixa`; Decimal; totais e saldo livre |
| [validacao](validacao/spec.md) | VAL | vigente | Validação do JSON com todos os erros e caminho |
| [exportacao](exportacao/spec.md) | EXP | vigente | `--formato`, CSV de lançamentos e de resumo |
| [planilha](planilha/spec.md) | PLN | vigente | `.xlsx`: Resumo Geral, abas por mês, gráficos |
| [armazenamento](armazenamento/spec.md) | STO | vigente (implementado) | Banco SQLite, centavos, usuários, lixeira, importar/exportar JSON |
| [api](api/spec.md) | WEB | vigente (implementado) | API HTTP, login/sessão/CSRF, lançamentos, painéis, downloads, lixeira, contrato OpenAPI (Fase 3) |
| [frontend](frontend/spec.md) | WEB | rascunho | Telas React/TypeScript: login, mês, ano, lixeira, arquivos (Fase 4; vira vigente na última etapa) |
| [interface-web](interface-web/spec.md) | WEB | rascunho | Execução local e hospedada (`controlegastos web`, Docker) e plano geral (`design.md`, `tasks.md`) |

## Convenções

- Cada requisito é uma linha `**XXX-NN**` (código da capacidade + número, nunca reaproveitado). Cenários usam **Dado / Quando / Então**.
- `status`: `vigente` (verificado por testes), `rascunho` (decisões e requisitos escritos, ainda não implementados; o CI não exige testes) ou `adiado`. Um spec vira `vigente` no commit que começa a implementá-lo.
- **Todo ID de um spec vigente precisa ser citado em ao menos um teste**, com o comentário `# Spec: VAL-03` acima do teste (vários IDs separados por vírgula). `uv run python scripts/conferir_specs.py` confere isso, e o CI roda o mesmo teste (`tests/test_conferir_specs.py`). Citar um ID inexistente também falha.
- Valores de referência (totais do `data/entradas/exemplo.json`) são a verdade numérica: viram asserções, não texto solto.
- Dinheiro é sempre `Decimal` (ver LAN-02).

## Fluxo de uma mudança

1. **Levantar**: conversa curta para entender a intenção; dúvidas viram "Perguntas abertas" no spec.
2. **Spec primeiro**: edite o `spec.md` (novos IDs, nunca renumerar) em um commit só dele (o agente commita sozinho, em branch). Sem aprovação prévia quando decorre de decisões já registradas; se contrariar uma decisão registrada ou criar escopo novo, o agente pergunta ao usuário.
3. **Plano curto** no chat ou na descrição do PR. Mudança grande ganha `design.md` e `tasks.md` na pasta da capacidade.
4. **Testes primeiro**, citando os IDs; depois a implementação.
5. **Filtros automáticos**: hook de edição (`scripts/checar.py`) e CI (ruff, pytest, conferência de specs).
6. **Merge**: o agente mescla o próprio PR com o CI verde; o usuário pode revisar depois, e o histórico (commits de spec separados) permite desfazer.

Modelo para uma nova capacidade: [_modelo.md](_modelo.md).
