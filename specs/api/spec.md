---
capacidade: api
codigo: WEB
status: vigente
---

# Capacidade: API HTTP e autenticação

## Objetivo

Expor os casos de uso do sistema por HTTP/JSON, com login, para a interface web (e qualquer cliente) registrar e consultar lançamentos, ver painéis, baixar arquivos e importar/exportar JSON. Os IDs `WEB-xx` são os mesmos de `interface-web` (as partes de tela e de execução ficam lá: WEB-14, WEB-15, WEB-18). Rotas sob `/api`; textos de erro em português.

## Decisões

- FastAPI; dados via `armazenamento` (repositório por usuário). Sessão em cookie assinado; CSRF por cabeçalho; contas só por comando.
- Dinheiro trafega como texto decimal (`"1200.00"`), nunca como número JSON.
- Limite de tentativas de login guardado em memória do processo (suficiente para uma instância; trocar por armazenamento compartilhado se houver várias réplicas).

## Comportamento

Conta e sessão:

- **WEB-01** `POST /api/auth/login` com `{"nome","senha"}`: sucesso (200) grava a sessão em cookie assinado `HttpOnly` e `SameSite=Lax`, válido por 7 dias, e devolve `{"id","nome","csrf_token"}`. Usuário inexistente e senha errada dão o mesmo 401 e a mesma mensagem. Senhas são guardadas com Argon2. Não há cadastro público: contas só pelo comando `controlegastos usuario criar NOME` (senha pedida sem eco, confirmada duas vezes, com no mínimo 8 caracteres; nome repetido é recusado). `POST /api/auth/logout` encerra a sessão e `GET /api/me` devolve o usuário logado.
- **WEB-02** Toda rota de dados exige sessão válida; sem cookie, ou com cookie adulterado ou expirado, responde 401. Cada usuário só acessa os próprios dados (STO-06): recurso de outro usuário responde 404.
- **WEB-03** Requisições `POST`, `PUT`, `PATCH` e `DELETE` autenticadas exigem o cabeçalho `X-CSRF-Token` igual ao `csrf_token` da sessão; ausente ou diferente responde 403. No login, 5 falhas em 15 minutos para o mesmo nome e IP bloqueiam novas tentativas por 15 minutos (429 com `Retry-After` e mensagem em português); um login com sucesso zera o contador.
- **WEB-04** O cookie é `Secure` quando `CONTROLEGASTOS_COOKIE_SECURE=1`. Nesse modo hospedado a chave secreta (`CONTROLEGASTOS_CHAVE_SECRETA`) é obrigatória e o app se recusa a subir sem ela; no modo local, sem chave, gera uma aleatória por processo.

Lançamentos e meses:

- **WEB-05** `POST /api/lancamentos` (201) com `ano, mes, tipo, descricao, valor, dia` e opcionais `categoria, tipo_investimento, ativo`; `PATCH /api/lancamentos/{id}` altera campos; `DELETE /api/lancamentos/{id}` (204) manda para a lixeira (STO-12). Id inexistente, de outro usuário ou já na lixeira responde 404.
- **WEB-06** `GET /api/meses/{ano}/{mes}` devolve salário, meta, os lançamentos vivos ordenados por dia e id, e os totais (`receitas`, `despesas`, `investimentos`, `saldo_livre`, com a regra de LAN-03; o salário conta como receita, LAN-01). Mês sem dados responde 200 com tudo vazio.
- **WEB-07** `PUT /api/meses/{ano}/{mes}` define `salario` e/ou `meta_investimento` (texto decimal, ou `null` para limpar); o que não for enviado não muda.
- **WEB-08** Erros de validação (corpo malformado ou regras VAL-*) respondem 422 com `{"erros":[{"caminho","mensagem"}]}`, todos de uma vez, em português, com o caminho relativo ao campo (ex.: `valor`); nada é gravado.

Painéis:

- **WEB-09** O mesmo `GET /api/meses/{ano}/{mes}` traz `investimentos_por_classe` (tipo, total e percentual do total investido, como na aba do mês, PLN-04) e `meta` (`valor`, `investido`, `diferenca = meta - investido` e `situacao` `falta` ou `acima`), presente só quando há meta.
- **WEB-10** `GET /api/anos/{ano}/resumo` devolve o resumo de cada mês (receitas, despesas, investimentos, saldo livre), `patrimonio`, `ranking` de categorias (com `Sem categoria`) e `variacao` do saldo, pelas mesmas funções e regras de PLN-06 a PLN-09. Ano sem dados responde 200 com listas vazias.
- **WEB-11** Os números da API vêm do mesmo cálculo do `.xlsx` e do CSV (`LivroCaixa` e `resumo.py`); o front-end nunca recalcula totais.

Arquivos:

- **WEB-12** `GET /api/exportar/xlsx` devolve a planilha e `GET /api/exportar/csv` um `.zip` com os dois CSV; ambos aceitam `?ano=` para limitar a um ano, são gerados em memória e trazem `Content-Disposition` com o nome do arquivo.
- **WEB-13** `POST /api/importar/json?substituir=false` recebe o documento JSON de entrada e devolve `{"lancamentos_criados","meses":[{"ano","mes"}],"substituidos"}`; erros de validação dão 422 (WEB-08); meses que já existem dão 409 com a lista deles, sem gravar nada, a menos que `substituir=true` (STO-08). `GET /api/exportar/json` devolve o documento do usuário (STO-09).
- **WEB-19** Lixeira: `GET /api/lixeira` lista; `POST /api/lixeira/{id}/restaurar`; `DELETE /api/lixeira/{id}` exclui definitivamente (204); `DELETE /api/lixeira` esvazia e devolve `{"removidos": n}`. Itens da lixeira nunca aparecem nos totais, painéis ou arquivos.

Contrato:

- **WEB-16** O contrato é o OpenAPI do app (`/openapi.json`). Um instantâneo versionado em `specs/api/openapi.json` é conferido por teste e regenerado com `uv run python scripts/exportar_openapi.py`; o cliente TypeScript (Fase 4) é gerado dele.
- **WEB-17** Na saída, todo valor monetário é texto com duas casas (`"1200.00"`); na entrada, valores monetários só são aceitos como texto decimal. Número JSON onde se espera dinheiro é erro 422.

## Valores de referência

Importado o `data/entradas/exemplo.json`, `GET /api/meses/2025/1` devolve totais `receitas "5250.00"`, `despesas "1780.00"`, `investimentos "1000.00"`, `saldo_livre "2470.00"` e meta `valor "1000.00"`, `diferenca "0.00"`.

## Fora de escopo

- Cadastro público, recuperação de senha, OAuth, vários usuários simultâneos com papéis.
- Paginação (o volume por mês é pequeno).

## Perguntas abertas

Nenhuma pendente.

## Rastreabilidade

`src/controlegastos/web/`, `resumo.py`, `armazenamento/`; testes `test_api_*.py`.
