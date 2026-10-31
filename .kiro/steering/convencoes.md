# Convenções

O [AGENTS.md](../../AGENTS.md) é a fonte de verdade. Se este arquivo contradisser o AGENTS.md, siga o AGENTS.md e corrija este arquivo.

## Regras obrigatórias

1. Valores monetários são `Decimal`, nunca `float`. A conversão para `float` só acontece na hora de gravar células do openpyxl.
2. Nunca crie commits, `git add` ou `git push` sem pedido explícito do usuário.
3. Ao mudar o esquema de dados, atualize juntos, na mesma mudança: `loader.py`, `validador.py`, `data/entradas/exemplo.json` e `AGENTS.md`.
4. Documentação e mensagens ao usuário em português.
5. Convenção financeira: `saldo_livre = receitas - despesas - investimentos`.
6. Depois de mexer em dependências, rode `uv sync` e valide com uma geração de planilha.
7. Fixe versões de dependências novas com limites (`>=X,<Y`) e mantenha o `uv.lock` atualizado.

## Nomenclatura

O AGENTS.md pede identificadores em inglês, mas o código existente usa português (`LivroCaixa`, `carregar_json`, `gerar_planilha`). Para manter a consistência, os módulos novos seguem o padrão português já usado no pacote. Essa divergência é pré-existente e fica registrada aqui; uma eventual migração para inglês deve ser uma mudança à parte, pedida pelo usuário.

## Qualidade

- Toda mudança de código passa por `uv run ruff check .` e `uv run pytest`.
- Testes não iniciam a interface web nem importam `streamlit`.
- Dados pessoais (`data/entradas/20*.json`) nunca entram em commits, imagens ou exemplos.
