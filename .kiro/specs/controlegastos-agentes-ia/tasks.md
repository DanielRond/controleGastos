# Implementation Plan: controlegastos-agentes-ia

## Overview

Este plano organiza o ambiente do controleGastos, a configuração para agentes de IA no Kiro e as features do roadmap, na ordem de prioridade A (validação de schema), B (exportação CSV), C (interface web) e E (gráficos extras). A linguagem de implementação é Python 3.14, com uv, openpyxl, pytest, ruff e hypothesis (propriedades).

Regras que valem para todas as tarefas:

- Valores monetários usam Decimal. Nenhum commit, `git add` ou `git push` é feito sem pedido explícito do usuário.
- Cada instalação de ferramenta exige confirmação separada do usuário, pedida por meio da ferramenta de entrada do usuário.
- Ao mudar o esquema de dados, `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` são atualizados na mesma mudança.
- A importação de extratos bancários está fora do escopo desta fase.
- Os testes não iniciam a interface web nem importam `streamlit`.
- Tarefas de teste de propriedade (hypothesis) e testes unitários são sub-tarefas opcionais, marcadas com `*`.

## Tasks

- [x] 1. Preparar o ambiente e a raiz do workspace
  - [x] 1.1 Verificar a instalação do git
    - Executar `git --version`. Se falhar, executar `winget list --id Git.Git`, verificar se o instalador iniciado antes ainda está em execução e aguardar sua conclusão
    - Recarregar o `PATH` a partir do registro e procurar `git.exe` no caminho padrão de instalação
    - Se o git continuar ausente, registrar como pendente e perguntar ao usuário, por ferramenta de entrada, se deve reinstalar via winget
    - Não executar nenhuma etapa de git antes de `git --version` ter sucesso
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.2 Pré-checar conflitos e mover `controleGastos-main` para a raiz
    - Listar os itens de primeiro nível de `controleGastos-main` e verificar se algum já existe na raiz; havendo conflito, interromper antes de mover e listar os conflitos ao usuário
    - Gerar o manifesto de integridade (caminho relativo e SHA-256 de cada arquivo) com `Get-FileHash`
    - Mover cada item com `Move-Item` sem `-Force`, preservando `.kiro/` e `.kiro/specs`
    - Se um movimento falhar no meio, parar e informar o que foi movido e o que falta
    - _Requisitos: 1.1, 1.4, 1.5_

  - [x] 1.3 Verificar a integridade e remover a pasta vazia
    - Recalcular os hashes na raiz e compará-los com o manifesto
    - Remover `controleGastos-main` com `Remove-Item` sem `-Recurse`
    - Confirmar que `pyproject.toml`, `src/`, `tests/`, `data/`, `docs/`, `.github/`, `AGENTS.md` e `README.md` estão na raiz
    - _Requisitos: 1.1, 1.2, 1.3, 1.5_

  - [x] 1.4 Instalar uv e Python 3.14 com confirmação por ferramenta
    - Detectar cada ferramenta (`Get-Command uv`, `uv python list` ou `py -3.14 --version`) e pular as já disponíveis
    - Conferir os IDs com `winget search` e pedir uma confirmação separada ao usuário, por ferramenta de entrada, antes de cada `winget install`
    - Verificar a versão depois de cada instalação (`uv --version`, `python --version` com 3.14); se o `PATH` não atualizar, recarregá-lo do registro
    - Registrar como pendente a ferramenta recusada ou que falhou
    - _Requisitos: 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 1.5 Inicializar o git e configurar o remoto sem commits
    - Executar `git init` somente se não existir `.git`; confirmar que o `.gitignore` está na raiz
    - Se o usuário informar uma URL, configurar `origin` passando a URL como argumento único; se `origin` já existir com outra URL, perguntar antes de `git remote set-url`
    - Relatar o estado com `git status`, sem executar `git add`, `git commit` ou `git push`
    - _Requisitos: 3.1, 3.2, 3.3, 3.4_

  - [x] 1.6 Executar a linha de base
    - Executar, na raiz e nesta ordem, `uv sync`, `uv run ruff check .` e `uv run pytest`
    - Registrar sucesso ou falha de cada comando e a quantidade de testes aprovados e reprovados
    - Se algum comando falhar, relatar o comando e a saída de erro e não iniciar a implementação; se uv ou Python 3.14 estiverem pendentes, relatar a linha de base como pendente
    - _Requisitos: 4.1, 4.2, 4.3_

- [x] 2. Criar o steering do projeto
  - [x] 2.1 Criar `.kiro/steering/produto.md`
    - Descrever propósito, público-alvo, saída principal em .xlsx com CSV e interface web como complementos
    - Registrar o roadmap na ordem A, B, C, E e declarar a importação de extratos bancários como fora do escopo desta fase
    - _Requisitos: 5.1, 5.2, 5.7_

  - [x] 2.2 Criar `.kiro/steering/tech.md`
    - Listar Python >= 3.14, uv, openpyxl, pytest, ruff, o extra opcional `ui` e os comandos `uv sync`, `uv run pytest` e `uv run ruff check .`
    - _Requisitos: 5.1, 5.3_

  - [x] 2.3 Criar `.kiro/steering/estrutura.md`
    - Descrever as responsabilidades de `cli.py`, `loader.py`, `modelo.py`, `generator.py` e dos módulos novos, e dos diretórios `tests/`, `data/entradas/`, `docs/media/` e `saida/`
    - Resumir e apontar para o `AGENTS.md` em vez de copiar o esquema JSON
    - _Requisitos: 5.1, 5.4, 5.8_

  - [x] 2.4 Criar `.kiro/steering/convencoes.md`
    - Registrar: Decimal para valores monetários, nenhum commit sem pedido explícito, atualização conjunta de `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md`, código em inglês e documentação e mensagens em português
    - Registrar `saldo_livre = receitas - despesas - investimentos` e que o AGENTS.md prevalece em caso de conflito
    - Registrar que os módulos novos seguem a nomenclatura em português já usada no pacote e sinalizar essa divergência pré-existente ao usuário
    - _Requisitos: 5.1, 5.5, 5.6, 5.8_

- [x] 3. Criar agentes por papel e hooks
  - [x] 3.1 Conferir o formato suportado de agentes e hooks
    - Consultar a documentação do Kiro e a versão instalada para confirmar pasta, campos e restrição de ferramentas dos agentes em `.kiro/agents`
    - Confirmar o formato dos hooks, os gatilhos disponíveis (`PostFileSave`) e se existe gatilho de acionamento manual; confirmar se o shell aceita `&&` ou se é preciso usar `cmd /c`
    - Definir os fallbacks previstos no design se algum formato não for suportado e registrar a decisão ao usuário
    - _Requisitos: 6.1, 7.3, 7.4_

  - [x] 3.2 Criar os quatro agentes em `.kiro/agents`
    - Criar `planejador` (só specs, sem alterar `src/`), `implementador` (ler steering e `tasks.md` antes de alterar código), `qa` (executar e relatar `uv run pytest` e `uv run ruff check .`) e `documentacao` (atuar só em `README.md`, `AGENTS.md`, `docs/` e steering)
    - Incluir em cada prompt as regras "nunca criar commits sem pedido explícito" e "valores monetários usam Decimal", com referência aos arquivos de steering
    - _Requisitos: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7_

  - [x] 3.3 Criar os três hooks em `.kiro/hooks`
    - Nota: o Kiro atual não tem hook de acionamento manual; a revisão de documentação virou o steering manual `.kiro/steering/revisar-documentacao.md` (comando `/revisar-documentacao`)
    - `checar-ao-salvar`: ao salvar arquivo `.py` em `src/` ou `tests/`, executar `uv run ruff check .` e `uv run pytest`, exibindo a saída em caso de falha
    - `lembrete-esquema`: ao salvar `loader.py`, `validador.py` ou `exemplo*.json`, lembrar de atualizar `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` em conjunto
    - `revisar-documentacao`: acionamento somente manual, com prompt de revisão de `README.md`, `AGENTS.md` e steering
    - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 4. Implementar a validação de schema (feature A)
  - [x] 4.1 Conferir os exemplos e adicionar o hypothesis
    - Antes de implementar, verificar os campos de `data/entradas/exemplo.json` e `exemplo-completo.json` contra as regras do design (campos obrigatórios, `dia`, tipos numéricos, `tipo` de investimento) e relatar divergências; corrigir os exemplos apenas se necessário e junto com o `AGENTS.md`
    - Adicionar `hypothesis` ao grupo `dev` do `pyproject.toml` com versão pinada (`uv add --dev hypothesis==<versão>`)
    - _Requisitos: 8.13, 8.14_

  - [x] 4.2 Criar `src/controlegastos/validador.py`
    - Implementar `ErroDeValidacao`, `TIPOS_DE_INVESTIMENTO_CONHECIDOS` e `validar(dados)` apenas com a biblioteca padrão, sem importar outros módulos do pacote
    - Verificar `anos`, `ano`, `meses`, `mes` entre 1 e 12, `dia` válido com `calendar.monthrange` (29/02 só em ano bissexto), valores numéricos finitos e não booleanos, campos obrigatórios e tipo de investimento conhecido
    - Reportar todos os erros em português com Caminho_do_Erro (`anos[0].meses[2].despesas[1].valor`) e nunca lançar por causa do conteúdo (raiz inválida gera o caminho `(raiz)`)
    - _Requisitos: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8, 8.9_

  - [x] 4.3 Integrar o validador ao `loader.py`
    - Criar `ErroDeValidacaoJSON(ValueError)` com a lista de erros e `carregar_dados(dados)` que valida antes de construir o `LivroCaixa`
    - Fazer `carregar_json` ler o arquivo e delegar para `carregar_dados`, mantendo a assinatura pública, com mensagem em português para JSON ilegível
    - _Requisitos: 8.10, 8.14_

  - [x] 4.4 Integrar o validador ao `cli.py`
    - Capturar `ErroDeValidacaoJSON` antes do tratamento genérico, exibir todas as mensagens (uma por linha) e retornar 1 sem criar arquivos
    - Manter o comportamento atual e o código 0 para entradas válidas
    - _Requisitos: 8.11, 8.12_

  - [x]* 4.5 Escrever testes unitários do validador
    - Em `tests/test_validador.py`, cobrir um caso válido e um inválido por regra dos critérios 8.2 a 8.7, 29/02 em 2024 (válido) e 2025 (inválido), raiz que não é objeto e booleano em `valor`
    - Verificar que `exemplo.json` e `exemplo-completo.json` não geram erros
    - _Requisitos: 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.13, 8.15_

  - [x]* 4.6 Escrever testes unitários de loader e CLI para validação
    - Em `tests/test_loader.py` e `tests/test_cli.py`, verificar que `ErroDeValidacaoJSON` carrega todos os erros, que a entrada inválida retorna 1 com todas as mensagens (`caplog`) e que a entrada válida retorna 0
    - Confirmar que os testes existentes continuam passando
    - _Requisitos: 8.10, 8.11, 8.12_

  - [x]* 4.7 Escrever teste de propriedade para documentos válidos
    - Em `tests/test_validador_propriedades.py`, criar a estratégia `documentos_validos()` e a violação para a próxima propriedade
    - **Property 1: Documentos válidos não geram erros**
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.13**

  - [x]* 4.8 Escrever teste de propriedade para violação injetada
    - **Property 2: Uma violação injetada é reportada no caminho correto**
    - **Validates: Requirements 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8**

  - [x]* 4.9 Escrever teste de propriedade para múltiplos erros
    - **Property 3: Todos os erros são reportados em uma única execução**
    - **Validates: Requirements 8.9**

  - [x]* 4.10 Escrever teste de propriedade para rejeição antes da construção
    - Em `tests/test_cli_propriedades.py`, verificar `carregar_dados`, o retorno 1 da CLI e a ausência de arquivos de saída
    - **Property 4: Entrada inválida é rejeitada antes da construção e o CLI retorna 1**
    - **Validates: Requirements 8.10, 8.11, 8.12**

- [x] 5. Checkpoint - Validação de schema
  - Ensure all tests pass, ask the user if questions arise.

- [x] 6. Implementar a exportação CSV (feature B)
  - [x] 6.1 Criar `src/controlegastos/exportador_csv.py`
    - Implementar `caminhos_csv`, `formatar_decimal` (duas casas, ROUND_HALF_UP, ponto), `linhas_lancamentos`, `linhas_resumo` e `exportar_csv`
    - Gravar com UTF-8, `newline=""` e `lineterminator="\n"`, criar o diretório de destino e usar `data` em `AAAA-MM-DD` e `tipo` em `receita`, `despesa` ou `investimento`
    - Calcular o resumo com `Mes.total_receitas`, `total_despesas`, `total_investimentos` e `saldo_livre`, quantizando apenas na formatação
    - _Requisitos: 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10_

  - [x] 6.2 Adicionar a opção `--formato` ao `cli.py`
    - Adicionar `--formato` com `xlsx` (padrão), `csv` e `ambos`, gerar conforme o valor e imprimir uma linha `Arquivo disponível em: <caminho>` por arquivo gerado
    - Exibir mensagem em português para valor inválido e sair com código diferente de 0
    - _Requisitos: 9.1, 9.2, 9.11, 9.12_

  - [x]* 6.3 Escrever testes unitários do exportador e da opção `--formato`
    - Em `tests/test_exportador_csv.py` e `tests/test_cli.py`, verificar cabeçalhos exatos, `Decimal("1200")` como `1200.00`, arredondamento half-up, criação do diretório, decodificação UTF-8 e nomes derivados de `-o`
    - Verificar o padrão `xlsx`, `csv`, `ambos` (3 caminhos) e o valor inválido
    - _Requisitos: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.10, 9.11, 9.12, 9.13_

  - [x]* 6.4 Escrever teste de propriedade para o round trip do CSV de lançamentos
    - Em `tests/test_exportador_csv_propriedades.py`, incluir textos com vírgulas, aspas, quebras de linha e Unicode
    - **Property 5: Round trip do CSV de lançamentos**
    - **Validates: Requirements 9.3, 9.5, 9.6, 9.7, 9.8**

  - [x]* 6.5 Escrever teste de propriedade para os totais do CSV de resumo
    - Gerar a planilha em `tmp_path`, ler o Resumo Geral com openpyxl e comparar o saldo arredondado a duas casas
    - **Property 6: Totais do CSV de resumo coincidem com o modelo e com o Resumo Geral**
    - **Validates: Requirements 9.4, 9.9**

- [x] 7. Checkpoint - Exportação CSV
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 8. Implementar a interface web (feature C)
  - [ ] 8.1 Verificar a compatibilidade do Streamlit com Python 3.14
    - Antes de qualquer código de UI, executar `uv sync --extra ui` (após 8.2 provisório) ou `uv pip install streamlit` em ambiente descartável e `uv run streamlit hello` em Python 3.14, e anotar versões compatíveis
    - Se falhar, relatar ao usuário e propor a contingência do design (versão mais nova do Streamlit ou outro framework), mantendo o Servico_Core intacto, e registrar a escolha final no `design.md`
    - _Requisitos: 10.2, 10.3_

  - [ ] 8.2 Declarar o extra opcional `ui` no `pyproject.toml`
    - Adicionar `[project.optional-dependencies] ui = ["streamlit>=X,<Y"]` com os limites definidos em 8.1, mantendo `dependencies` apenas com `openpyxl`, e atualizar o `uv.lock`
    - _Requisitos: 10.2_

  - [ ] 8.3 Criar `src/controlegastos/servico.py`
    - Implementar `ResultadoCarga`, `carregar_de_bytes`, `validar_dados`, `novo_documento`, `adicionar_lancamento` (devolve cópia profunda), `salvar_json` (nome sanitizado, `FileExistsError` sem `sobrescrever`), `gerar_arquivos` e `gerar_em_memoria`
    - Fazer `salvar_json` e `gerar_arquivos` validarem antes de escrever e levantarem `ErroDeValidacaoJSON` sem criar arquivos
    - Não importar `streamlit` nem `interface_web`
    - _Requisitos: 10.5, 10.7, 10.8, 10.9, 10.10, 10.11, 10.13_

  - [ ]* 8.4 Escrever testes unitários do Servico_Core
    - Em `tests/test_servico.py`, verificar que `adicionar_lancamento` não altera o original, que `salvar_json` recusa `../x` e sobrescrita sem confirmação, que `gerar_em_memoria` retorna três arquivos e que importar `servico` não carrega `streamlit` (`sys.modules`)
    - _Requisitos: 10.8, 10.9, 10.10, 10.11, 10.12_

  - [ ] 8.5 Criar `src/controlegastos/interface_web.py`
    - Único módulo que importa `streamlit`: upload de JSON, formulário de novo lançamento, tabela de erros (Caminho e Mensagem), botões Salvar e Gerar desabilitados com erros e três `st.download_button`
    - Manter o estado anterior da sessão quando `erro_leitura` não for `None`
    - _Requisitos: 10.5, 10.6, 10.7, 10.8, 10.9, 10.10, 10.13_

  - [ ] 8.6 Adicionar o subcomando `ui` ao `cli.py`
    - Verificar `importlib.util.find_spec("streamlit")`; se ausente, imprimir em português o comando `uv sync --extra ui` e retornar 1
    - Se presente, executar `streamlit run` de `interface_web.py` em subprocesso, sem importar `streamlit` no `cli.py`
    - _Requisitos: 10.1, 10.4_

  - [ ]* 8.7 Escrever teste unitário do subcomando `ui` sem dependência
    - Em `tests/test_cli.py`, simular a ausência de `streamlit` com `monkeypatch` em `find_spec` e verificar código diferente de 0 e a mensagem com o comando de instalação
    - _Requisitos: 10.4_

  - [ ]* 8.8 Escrever teste de propriedade para salvar e recarregar
    - Em `tests/test_servico_propriedades.py`
    - **Property 7: Salvar e recarregar preserva o documento**
    - **Validates: Requirements 10.5, 10.8**

  - [ ]* 8.9 Escrever teste de propriedade para dados inválidos
    - **Property 8: Dados inválidos nunca geram nem salvam arquivos**
    - **Validates: Requirements 10.7, 10.9**

  - [ ]* 8.10 Escrever teste de propriedade para conteúdo ilegível
    - **Property 9: Conteúdo ilegível não altera a sessão**
    - **Validates: Requirements 10.13**

- [ ] 9. Checkpoint - Interface web
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 10. Implementar os gráficos extras (feature E)
  - [x] 10.1 Criar as funções puras de dados em `generator.py`
    - Implementar `_patrimonio_acumulado`, `_ranking_despesas` (rótulo `Sem categoria` para categoria vazia, só espaços ou `geral`; ordem decrescente com desempate por nome) e `_variacao_saldo`, usando Decimal
    - _Requisitos: 11.1, 11.2, 11.3, 11.6_

  - [x] 10.2 Estender a Area_de_Apoio e criar os três gráficos
    - Gravar os blocos de apoio em `W:X`, `Z:AA` e `AC:AD` com `float(valor)` e formato `#,##0.00`, sem alterar as tabelas existentes em `Q:U`
    - Criar com openpyxl o `LineChart` de patrimônio (âncora `A42`), o `BarChart` horizontal de ranking limitado a 10 categorias (`A62`) e o `BarChart` de comparativo (`A82`), cada um apenas quando sua condição de dados for satisfeita, sem lançar erro
    - Manter a pizza em `A2` e as barras mensais em `A22`
    - _Requisitos: 11.1, 11.2, 11.3, 11.4, 11.5, 11.7, 11.8_

  - [x]* 10.3 Escrever testes unitários dos gráficos
    - Em `tests/test_generator.py`, verificar 5 gráficos na aba `Gráficos` para `exemplo-completo.json` (confirmar a premissa de dados suficientes), somente pizza e barras para um livro com um mês, e que os testes existentes continuam verdes
    - _Requisitos: 11.7, 11.8, 11.9_

  - [x]* 10.4 Escrever teste de propriedade para o ranking de despesas
    - Em `tests/test_generator_propriedades.py`
    - **Property 10: Ranking de despesas ordenado, completo e com rótulo padrão**
    - **Validates: Requirements 11.2, 11.6**

  - [x]* 10.5 Escrever teste de propriedade para o patrimônio acumulado
    - **Property 11: Patrimônio acumulado é a soma cumulativa dos aportes**
    - **Validates: Requirements 11.1**

  - [x]* 10.6 Escrever teste de propriedade para dados insuficientes
    - Incluir livro vazio, com um mês, sem despesas e sem investimentos
    - **Property 12: Gerar a planilha nunca falha por dados insuficientes**
    - **Validates: Requirements 11.3, 11.7, 11.8**

  - [ ] 10.7 Atualizar as imagens em `docs/media`
    - Gerar a planilha a partir de `exemplo-completo.json` (dados fictícios) e atualizar as imagens para incluir os novos gráficos; se não for possível renderizar as imagens no ambiente, relatar ao usuário como pendência manual
    - _Requisitos: 11.10_

- [ ] 11. Checkpoint - Gráficos extras
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 12. Fechamento da fase
  - [ ] 12.1 Atualizar o `README.md`
    - Documentar `validador.py`, `exportador_csv.py`, `servico.py`, `interface_web.py`, `--formato`, o subcomando `ui`, o extra `ui`, os gráficos extras e a limitação do CSV no Excel pt-BR
    - Manter o Roadmap sem marcar features até 12.6 e registrar a importação de extratos bancários como fora de escopo
    - _Requisitos: 12.1, 12.8_

  - [ ] 12.2 Atualizar o `AGENTS.md`
    - Refletir novos módulos, subcomandos, opções, dependências, regras de validação e a atualização conjunta de `loader.py`, `validador.py` e `exemplo.json`
    - _Requisitos: 12.1, 8.14_

  - [ ] 12.3 Atualizar o CI em `.github/workflows/ci.yml`
    - Manter `uv sync`, `uv run ruff check .` e `uv run pytest` cobrindo os módulos novos
    - Adicionar o job `ui-import` com `uv sync --extra ui`, `uv run python -c "import streamlit"` e `continue-on-error: true`
    - _Requisitos: 12.3, 12.4_

  - [ ] 12.4 Executar a suíte completa
    - Executar `uv run pytest` e `uv run ruff check .` e relatar o resultado; se falhar, relatar a falha ao usuário
    - _Requisitos: 12.5, 12.7_

  - [ ] 12.5 Executar a geração ponta a ponta
    - Executar `uv run controlegastos gerar data/entradas/exemplo-completo.json -o saida/planilha.xlsx --formato ambos` e verificar a existência do .xlsx e dos dois CSV; se falhar, relatar ao usuário
    - _Requisitos: 12.6, 12.7_

  - [ ] 12.6 Marcar o Roadmap no `README.md`
    - Marcar como concluídas somente as features cuja suíte e geração ponta a ponta passaram; manter sem marcar as afetadas por falhas
    - _Requisitos: 12.2, 12.7_

- [ ] 13. Checkpoint final - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tarefas marcadas com `*` são opcionais e podem ser puladas para um MVP mais rápido.
- Cada tarefa referencia requisitos específicos para rastreabilidade.
- Os checkpoints validam o progresso de forma incremental após cada feature.
- Testes de propriedade validam propriedades universais de correção (mínimo de 100 exemplos, com o comentário `# Feature: controlegastos-agentes-ia, Property N: <título>`).
- Testes unitários validam exemplos e casos de borda.
- As tarefas do grupo 1 usam terminal e pedem confirmação do usuário antes de instalar ferramentas; as demais não fazem commits.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2"] },
    { "id": 2, "tasks": ["1.3"] },
    { "id": 3, "tasks": ["1.4"] },
    { "id": 4, "tasks": ["1.5"] },
    { "id": 5, "tasks": ["1.6"] },
    { "id": 6, "tasks": ["2.1", "2.2", "2.3", "2.4", "3.1"] },
    { "id": 7, "tasks": ["3.2", "3.3"] },
    { "id": 8, "tasks": ["4.1"] },
    { "id": 9, "tasks": ["4.2"] },
    { "id": 10, "tasks": ["4.3", "4.5"] },
    { "id": 11, "tasks": ["4.4", "4.7"] },
    { "id": 12, "tasks": ["4.6", "4.8"] },
    { "id": 13, "tasks": ["4.9", "4.10"] },
    { "id": 14, "tasks": ["6.1"] },
    { "id": 15, "tasks": ["6.2"] },
    { "id": 16, "tasks": ["6.3", "6.4"] },
    { "id": 17, "tasks": ["6.5"] },
    { "id": 18, "tasks": ["8.1"] },
    { "id": 19, "tasks": ["8.2"] },
    { "id": 20, "tasks": ["8.3"] },
    { "id": 21, "tasks": ["8.4", "8.5", "8.8"] },
    { "id": 22, "tasks": ["8.6", "8.9"] },
    { "id": 23, "tasks": ["8.7", "8.10"] },
    { "id": 24, "tasks": ["10.1"] },
    { "id": 25, "tasks": ["10.2"] },
    { "id": 26, "tasks": ["10.3", "10.4"] },
    { "id": 27, "tasks": ["10.5", "10.7"] },
    { "id": 28, "tasks": ["10.6"] },
    { "id": 29, "tasks": ["12.1", "12.2", "12.3"] },
    { "id": 30, "tasks": ["12.4", "12.5"] },
    { "id": 31, "tasks": ["12.6"] }
  ]
}
```
