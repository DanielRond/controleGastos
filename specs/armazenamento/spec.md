---
capacidade: armazenamento
codigo: STO
status: rascunho
---

# Capacidade: armazenamento

## Objetivo

Guardar os lançamentos de forma segura e consultável quando houver interface web e vários usuários, mantendo o JSON como formato de importação, exportação e backup versionável. **Rascunho: aguardando aprovação do usuário.**

## Decisões tomadas

- Banco de dados como fonte de verdade quando a web existir: **SQLite** por padrão, via SQLAlchemy 2, com migrações Alembic. Outro banco (ex.: Postgres) deve ser possível trocando só a configuração.
- O domínio (`modelo.py`, `LivroCaixa`) não muda: o armazenamento carrega do banco para um `LivroCaixa`, e planilha, CSV e totais continuam funcionando sem alteração.
- A CLI atual (`gerar` a partir de JSON) continua existindo.

## Comportamento

- **STO-01** O banco é configurável por `DATABASE_URL`; sem ela, usa um arquivo SQLite local. O código de domínio não conhece o banco.
- **STO-02** Valores monetários são guardados como inteiros em centavos e convertidos para `Decimal` nas bordas; nunca passam por `float`.
- **STO-03** Todo lançamento tem `id` estável gerado pelo sistema e pertence a um usuário (`user_id`); mês (salário e meta) é identificado por usuário, ano e mês.
- **STO-04** Cada lançamento tem `origem`: `manual` ou `importado_json` (reservado: `extrato`).
- **STO-05** Toda gravação é transacional: falha não deixa dados parciais.
- **STO-06** Nenhuma consulta retorna dados de outro usuário.
- **STO-07** O esquema evolui por migrações versionadas, aplicáveis por comando (`controlegastos banco atualizar`), sem perder dados.
- **STO-08** Importar JSON (formato atual): valida com as regras VAL-* e STO-11 antes de gravar, grava tudo ou nada e informa quantos lançamentos criou. Com erros, nada é gravado e todos os erros são devolvidos com caminho. Se o arquivo traz um mês que já existe para o usuário, a importação é **recusada** por padrão; com a opção explícita `substituir`, os meses do arquivo são trocados na mesma transação e os demais meses ficam intactos.
- **STO-09** Exportar JSON no formato atual. Round trip: importar e exportar produz um JSON que gera o mesmo `LivroCaixa` (mesmos totais).
- **STO-10** Carregar do banco para `LivroCaixa` de um usuário produz os mesmos totais que carregar o JSON equivalente (LAN-03).

- **STO-11** Valor com mais de duas casas decimais é rejeitado como erro de validação, no caminho do campo (`valor deve ter no máximo 2 casas decimais`), tanto na importação quanto nos formulários; nunca é arredondado em silêncio. Ao implementar, isso vira também o requisito **VAL-13** no spec de validação, com teste.

## Valores de referência

Importar `data/entradas/exemplo.json` e carregar do banco dá, em 2025-01, receitas 5250.00, despesas 1780.00, investimentos 1000.00, saldo livre 2470.00.

## Fora de escopo

- Importação de extratos bancários (fase posterior; STO-04 já reserva a origem).
- Múltiplas moedas.

## Perguntas abertas

1. Exclusão de lançamento: definitiva com confirmação, lixeira (exclusão lógica) ou desfazer? Proposta: definitiva com confirmação na v1, com o JSON exportado como backup.
