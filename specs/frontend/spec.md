---
capacidade: frontend
codigo: WEB
status: vigente
---

# Capacidade: telas da interface web

## Objetivo

As telas que o usuário usa no navegador: entrar, registrar e corrigir lançamentos, ver o mês e o ano, usar a lixeira e levar/trazer arquivos. Consomem só a API de [specs/api](../api/spec.md); nunca recalculam totais. **Vigente: cada requisito tem teste de componente (Vitest) e, onde há fluxo real, de ponta a ponta (Playwright).**

## Decisões

- SPA em React + TypeScript + Vite, em `frontend/`; cliente da API gerado de `specs/api/openapi.json` (`openapi-typescript` + `openapi-fetch`).
- Gráficos com ECharts. Estilo próprio, simples, sem framework de componentes.
- Em desenvolvimento o Vite faz proxy de `/api`; em produção a API serve os arquivos compilados (mesma origem, sem CORS).
- Testes: Vitest + Testing Library para unidades e componentes; Playwright para os fluxos reais, contra o app de verdade com SQLite temporário. Testes citam o ID com `// Spec: WEB-20`.

## Comportamento

- **WEB-18** Interface em pt-BR, valores em R$ no formato brasileiro (`R$ 1.200,50`), e navegável por teclado: todo campo tem rótulo associado, foco visível, ordem de tabulação lógica e mensagens de erro anunciadas (`role="alert"`).
- **WEB-20** Tela de login: nome e senha; erro de credenciais com mensagem genérica; bloqueio por tentativas (429) com mensagem clara; ao entrar, abre o mês atual.
- **WEB-21** Rotas protegidas: sem sessão, qualquer tela leva ao login (e volta para onde estava depois de entrar). O cabeçalho tem os links Mês, Ano, Lixeira, Arquivos e o botão Sair, que encerra a sessão.
- **WEB-22** Tela do mês: escolher ano e mês e navegar para o anterior e o seguinte; lista dos lançamentos por dia; totais (receitas, despesas, investimentos, saldo livre); investimentos por classe com percentual e a meta com o que falta; formulário de novo lançamento (investimento pede tipo e ativo), edição e exclusão. Erros de validação da API aparecem junto ao campo (WEB-08). Excluir move para a lixeira e avisa.
- **WEB-23** Na tela do mês é possível definir e limpar salário e meta de investimento.
- **WEB-24** Tela do ano: resumo mensal em tabela e três gráficos (evolução do patrimônio, ranking de categorias de despesa e variação do saldo livre), com os dados da API; ano sem dados mostra um aviso, não um erro.
- **WEB-25** Tela da lixeira: lista, restaura, exclui definitivamente e esvazia; excluir definitivamente e esvaziar pedem confirmação.
- **WEB-26** Tela de arquivos: baixar planilha e CSV (um ano ou todos), exportar JSON e importar JSON. A importação mostra quantos lançamentos criou; erros de validação aparecem com o caminho; se algum mês já existe, avisa e oferece "substituir os meses do arquivo" com confirmação.
- **WEB-27** Dinheiro no front: valores são tratados como texto decimal, sem aritmética com `number`; campos aceitam a digitação brasileira (`1.234,56` ou `1234,56`) e enviam `"1234.56"` à API; valor com mais de duas casas é recusado antes de enviar.

## Fora de escopo (v1)

- Tema escuro, internacionalização além do pt-BR, aplicativo móvel, modo offline.

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

`frontend/`; testes `frontend/src/**/*.test.ts(x)` e `frontend/e2e/*.spec.ts`.
