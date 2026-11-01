---
capacidade: interface-web
codigo: WEB
status: rascunho
---

# Capacidade: interface web

## Objetivo

Usar o controle de gastos de forma prática, sem editar JSON: entrar com login, registrar e corrigir lançamentos, ver o mês e o ano em painéis e baixar planilha e CSV. A CLI foi o ponto de partida e continua existindo. **Rascunho: aguardando aprovação do usuário.**

## Decisões tomadas

- Front-end **SPA** (opção B), separada da API; sem Streamlit.
- Back-end **FastAPI**; dados em SQLite (ver `armazenamento`).
- Deve rodar **localmente e hospedado**, com a mesma base de código.
- Autenticação com login; sem cadastro público na v1.
- Importação de extratos fica para depois da v1.
- Escopo da v1 confirmado: login, CRUD de lançamentos, painéis do mês e do ano, downloads, importar/exportar JSON.

## Comportamento

Autenticação e segurança:

- **WEB-01** Login com usuário e senha. Sessão por cookie `HttpOnly` e `SameSite=Lax`; senhas guardadas com Argon2. Não há cadastro público: contas são criadas por comando (`controlegastos usuario criar`).
- **WEB-02** Toda rota de dados exige sessão; sem sessão, responde 401. Um usuário só vê e altera os próprios dados (STO-06).
- **WEB-03** Operações que alteram dados têm proteção contra CSRF. Login limita tentativas: 5 falhas em 15 minutos por usuário e IP bloqueiam temporariamente, com mensagem em português.
- **WEB-04** O cookie é `Secure` quando configurado para HTTPS (obrigatório no modo hospedado).

Lançamentos:

- **WEB-05** Criar, editar e excluir lançamentos de receita, despesa e investimento (descrição, valor, dia, categoria; investimentos também têm tipo e ativo).
- **WEB-06** Listar os lançamentos de um mês, navegando entre meses, ordenados por dia, com os totais do mês.
- **WEB-07** Definir o salário e a meta de investimento do mês.
- **WEB-08** Erros de validação usam o contrato `caminho` + `mensagem` (VAL-09) e aparecem junto ao campo no formulário; nada é gravado enquanto houver erro.

Painéis:

- **WEB-09** Painel do mês: receitas, despesas, investimentos, saldo livre, investimentos por classe com %, meta e quanto falta.
- **WEB-10** Painel do ano: resumo por mês, evolução do patrimônio, ranking de categorias (com `Sem categoria`) e comparativo entre meses, com as mesmas regras de PLN-06 a PLN-09.
- **WEB-11** Os totais da web, do `.xlsx` e do CSV vêm do mesmo cálculo; nunca são recalculados no front-end.

Arquivos:

- **WEB-12** Baixar `.xlsx` e CSV (um ano ou todos), gerados em memória.
- **WEB-13** Importar JSON (STO-08) mostrando os erros por caminho, e exportar JSON (STO-09).

Execução e contrato:

- **WEB-14** Modo local: `uv run controlegastos web` sobe API e front no mesmo processo e origem, ligado a `127.0.0.1`, com SQLite local; o login continua exigido.
- **WEB-15** Modo hospedado: uma imagem Docker; configuração só por variáveis de ambiente (`DATABASE_URL`, chave secreta, cookie seguro); dados em volume; nenhum segredo no repositório.
- **WEB-16** A API tem contrato OpenAPI, e o front usa um cliente TypeScript **gerado** dele; o CI falha se o cliente estiver defasado.
- **WEB-17** Dinheiro trafega na API como texto decimal (`"1200.00"`), nunca como número JSON em ponto flutuante.
- **WEB-18** Interface em pt-BR, valores em R$ no formato brasileiro, e navegável por teclado com campos rotulados.

## Fora de escopo (v1)

- Importação de extratos bancários, várias moedas, categorias personalizadas, app mobile, cadastro público, recuperação de senha por e-mail.

## Perguntas abertas

1. **Framework da SPA.** Proposta: **React + TypeScript + Vite** (maior ecossistema e melhor suporte de agentes de IA). Alternativas: Vue ou Svelte.
2. Modo local exige login? Proposta: sim, para ser igual ao hospedado e simples de testar.
3. Haverá mais de um usuário já na v1, ou um só com o esquema pronto para vários? Proposta: esquema pronto (STO-03), uso de um usuário.

## Rastreabilidade

Ver `design.md` e `tasks.md` desta pasta. Ainda sem testes: o status `rascunho` isenta o CI até a aprovação.
