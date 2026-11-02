---
capacidade: interface-web
codigo: WEB
status: rascunho
---

# Capacidade: interface web

## Objetivo

Usar o controle de gastos de forma prática, sem editar JSON: entrar com login, registrar e corrigir lançamentos, ver o mês e o ano em painéis e baixar planilha e CSV. A CLI foi o ponto de partida e continua existindo. **Decisões aprovadas pelo usuário; permanece `rascunho` até começar a implementação da capacidade, quando passa a `vigente` e o CI exige um teste por requisito.**

## Decisões tomadas

- Front-end **SPA** (opção B), separada da API; sem Streamlit.
- Back-end **FastAPI**; dados em SQLite (ver `armazenamento`).
- Deve rodar **localmente e hospedado**, com a mesma base de código.
- Autenticação com login; sem cadastro público na v1.
- Importação de extratos fica para depois da v1.
- Front-end: **React + TypeScript + Vite** (confirmado).
- O login é exigido também no modo local, para ser igual ao hospedado (confirmado).
- Uma pessoa usa na v1, mas o esquema já suporta vários usuários (confirmado).
- Exclusão por **lixeira** com restauração, esvaziada só manualmente (confirmado).
- Escopo da v1 confirmado: login, CRUD de lançamentos, painéis do mês e do ano, downloads, importar/exportar JSON.

## Comportamento

Autenticação e segurança:

- **WEB-01** Login com usuário e senha. Sessão por cookie `HttpOnly` e `SameSite=Lax`; senhas guardadas com Argon2. Não há cadastro público: contas são criadas por comando (`controlegastos usuario criar`).
- **WEB-02** Toda rota de dados exige sessão; sem sessão, responde 401. Um usuário só vê e altera os próprios dados (STO-06).
- **WEB-03** Operações que alteram dados têm proteção contra CSRF. Login limita tentativas: 5 falhas em 15 minutos por usuário e IP bloqueiam temporariamente, com mensagem em português.
- **WEB-04** O cookie é `Secure` quando configurado para HTTPS (obrigatório no modo hospedado).

Lançamentos:

- **WEB-05** Criar, editar e excluir (para a lixeira, STO-12) lançamentos de receita, despesa e investimento (descrição, valor, dia, categoria; investimentos também têm tipo e ativo).
- **WEB-19** Tela de lixeira: lista os lançamentos apagados do usuário e permite restaurar, excluir definitivamente ou esvaziar a lixeira (esvaziar e excluir definitivamente pedem confirmação). Itens da lixeira nunca entram nos totais e painéis.
- **WEB-06** Listar os lançamentos de um mês, navegando entre meses, ordenados por dia, com os totais do mês.
- **WEB-07** Definir o salário e a meta de investimento do mês.
- **WEB-08** Erros de validação usam o contrato `caminho` + `mensagem` (VAL-09) e aparecem junto ao campo no formulário; nada é gravado enquanto houver erro. Valor com mais de duas casas decimais é um erro (STO-11).

Painéis:

- **WEB-09** Painel do mês: receitas, despesas, investimentos, saldo livre, investimentos por classe com %, meta e quanto falta.
- **WEB-10** Painel do ano: resumo por mês, evolução do patrimônio, ranking de categorias (com `Sem categoria`) e comparativo entre meses, com as mesmas regras de PLN-06 a PLN-09.
- **WEB-11** Os totais da web, do `.xlsx` e do CSV vêm do mesmo cálculo; nunca são recalculados no front-end.

Arquivos:

- **WEB-12** Baixar `.xlsx` e CSV (um ano ou todos), gerados em memória.
- **WEB-13** Importar JSON (STO-08) mostrando os erros por caminho, e exportar JSON (STO-09). Se algum mês do arquivo já existe, a importação é recusada e a tela oferece, de forma explícita, "substituir os meses do arquivo".

Execução e contrato:

- **WEB-14** Modo local: `uv run controlegastos web` sobe API e front no mesmo processo e origem, ligado a `127.0.0.1`, com SQLite local; o login continua exigido.
- **WEB-15** Modo hospedado: uma imagem Docker; configuração só por variáveis de ambiente (`DATABASE_URL`, chave secreta, cookie seguro); dados em volume; nenhum segredo no repositório.
- **WEB-16** A API tem contrato OpenAPI, e o front usa um cliente TypeScript **gerado** dele; o CI falha se o cliente estiver defasado.
- **WEB-17** Dinheiro trafega na API como texto decimal (`"1200.00"`), nunca como número JSON em ponto flutuante.
- **WEB-18** Interface em pt-BR, valores em R$ no formato brasileiro, e navegável por teclado com campos rotulados.

## Fora de escopo (v1)

- Importação de extratos bancários, várias moedas, categorias personalizadas, app mobile, cadastro público, recuperação de senha por e-mail.

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

Ver `design.md` e `tasks.md` desta pasta. Ainda sem testes: no status `rascunho` o CI não os exige. A base já pronta (Fase 1) está coberta por LAN-07, PLN-12, PLN-13 e EXP-12.
