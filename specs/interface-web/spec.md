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

As telas estão em [specs/frontend](../frontend/spec.md) (WEB-18 e WEB-20 a 27) e a API em [specs/api](../api/spec.md). Aqui ficam só os requisitos de execução, da Fase 5.

Execução:

- **WEB-14** Modo local: `uv run controlegastos web` sobe API e front no mesmo processo e origem, ligado a `127.0.0.1`, com SQLite local; o login continua exigido.
- **WEB-15** Modo hospedado: uma imagem Docker; configuração só por variáveis de ambiente (`DATABASE_URL`, chave secreta, cookie seguro); dados em volume; nenhum segredo no repositório.

## Fora de escopo (v1)

- Importação de extratos bancários, várias moedas, categorias personalizadas, app mobile, cadastro público, recuperação de senha por e-mail.

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

Ver `design.md` e `tasks.md` desta pasta. Ainda sem testes: no status `rascunho` o CI não os exige. A base já pronta (Fase 1) está coberta por LAN-07, PLN-12, PLN-13 e EXP-12.
