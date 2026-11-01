# Implementation Plan: controlegastos-agentes-ia

## Overview

Este plano organiza a configuração para agentes de IA no Kiro e as features do roadmap, na ordem A (validação de schema), B (exportação CSV) e E (gráficos extras). A interface web (C) foi adiada para outro PR; os IDs das tarefas foram mantidos, por isso há lacunas (3, 8 e 9). A linguagem de implementação é Python 3.14, com uv, openpyxl, pytest, ruff e hypothesis (propriedades).

Regras que valem para todas as tarefas:

- Valores monetários usam Decimal. Nenhum commit, `git add` ou `git push` é feito sem pedido explícito do usuário.
- Cada instalação de ferramenta exige confirmação separada do usuário, pedida por meio da ferramenta de entrada do usuário.
- Ao mudar o esquema de dados, `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` são atualizados na mesma mudança.
- A importação de extratos bancários está fora do escopo desta fase.
- Tarefas de teste de propriedade (hypothesis) e testes unitários são sub-tarefas opcionais, marcadas com `*`.

## Tasks

- [x] 1. Preparar o ambiente e a raiz do workspace (concluído; detalhes removidos)
  - _Requisitos: 1 a 4_

- [x] 2. Organizar o contexto para IA (inclui o antigo grupo 3)
  - [x] 2.1 Consolidar o contexto no `AGENTS.md` (fonte única, ~100 linhas) e remover os steerings duplicados; manter só `.kiro/steering/revisar-documentacao.md`
  - [x] 2.2 Criar os quatro agentes em `.kiro/agents`; o implementador não escreve em `.kiro/`, `.github/` e `AGENTS.md`
  - [x] 2.3 Criar os hooks portáveis: `checar-ao-salvar` (`scripts/checar.py`) e `lembrete-esquema`
  - _Requisitos: 5, 6, 7_

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

- [x] 10. Gráficos extras (feature E)
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

  - [x] 10.7 Atualizar as imagens em `docs/media`
    - Gerar a planilha a partir de `data/entradas/exemplo-completo.json` (dados fictícios) e atualizar as imagens para incluir os novos gráficos; se não for possível renderizar as imagens no ambiente, relatar ao usuário como pendência manual
    - Atenção: o `exemplo-completo.json` do working tree do usuário pode conter dados pessoais; usar a versão do git (`git show HEAD:data/entradas/exemplo-completo.json`)
    - _Requisitos: 11.10_

- [x] 11. Checkpoint - Gráficos extras

- [x] 12. Fechamento da fase
  - [x] 12.1 Atualizar o `README.md` (módulos, `--formato`, gráficos extras, limitação do CSV no Excel pt-BR, roadmap, fora de escopo)
    - _Requisitos: 12.1, 12.8_
  - [x] 12.2 Atualizar o `AGENTS.md` (feito junto com a consolidação do contexto)
    - _Requisitos: 12.1_
  - [x] 12.3 Conferir o CI: `uv sync`, `ruff`, `pytest`; sem job de UI
    - _Requisitos: 12.3, 12.4_
  - [x] 12.4 Executar a suíte completa
    - _Requisitos: 12.5, 12.7_
  - [x] 12.5 Executar a geração ponta a ponta com `--formato ambos`
    - _Requisitos: 12.6, 12.7_
  - [x] 12.6 Marcar o Roadmap no `README.md`
    - _Requisitos: 12.2, 12.7_

- [x] 13. Checkpoint final: CI verde no PR

## Notes

- Tarefas marcadas com `*` são opcionais.
- Testes de propriedade usam no mínimo 100 exemplos e o comentário `# Feature: controlegastos-agentes-ia, Property N: <título>`. As propriedades 7 a 9 (interface web) estão suspensas.
- Ninguém commita sem autorização; o versionamento é do agente principal, em commits pequenos e temáticos.

## Adiado (outro PR)

- Interface web (antigo grupo 8/9 e Requirement 10). Se for retomada: reavaliar o framework, pois o Streamlit foi descartado.
- Importação de extratos bancários.
