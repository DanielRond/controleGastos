# Requirements Document

## Introduction

Este documento define os requisitos para organizar o projeto controleGastos para desenvolvimento assistido por agentes de IA no Kiro e para evoluí-lo com as features do roadmap. O controleGastos é uma CLI Python (>= 3.14, gerenciada com uv, usando openpyxl, pytest e ruff) que gera planilhas .xlsx de gastos pessoais a partir de arquivos JSON.

O escopo desta fase cobre: (1) organização para IA (AGENTS.md como fonte única, agentes e hooks portáveis); (2) validação de schema do JSON; (3) exportação CSV; (4) gráficos extras; (5) fechamento (documentação, CI e verificação ponta a ponta).

FORA do escopo, adiados para outro PR ou fase: importação de extratos bancários e interface web (Requirement 10, descartado por ora; a numeração dos requisitos e das propriedades foi mantida porque os testes a citam).

Prioridade das features: (A) validação de schema, (B) exportação CSV, (E) gráficos extras.

## Glossary

- **Projeto**: O repositório controleGastos.
- **CLI**: A interface de linha de comando `controlegastos`, implementada em `cli.py` com argparse.
- **Loader**: O módulo `loader.py`, que converte o JSON em objetos `LivroCaixa`.
- **Modelo**: O módulo `modelo.py`, com as dataclasses Receita, Despesa, Investimento, Mes, Ano e LivroCaixa, que usam Decimal para valores monetários.
- **Gerador**: O módulo `generator.py`, que produz o arquivo .xlsx (Resumo Geral, abas por mês e Gráficos).
- **Validador**: O novo módulo `validador.py`, que verifica o schema do JSON de entrada.
- **Exportador_CSV**: O novo módulo responsável por gerar os arquivos CSV.
- **JSON_de_Entrada**: Arquivo JSON com lançamentos, seguindo o esquema documentado no AGENTS.md.
- **Caminho_do_Erro**: Texto que indica a posição do campo inválido no JSON, no formato `anos[0].meses[2].despesas[1].valor`.
- **Tipo_de_Investimento_Conhecido**: Um dos valores `renda_fixa`, `fii` ou `cripto`.
- **Saldo_Livre**: Valor calculado como receitas menos despesas menos investimentos.
- **CSV_de_Lancamentos**: Arquivo CSV com as colunas data, tipo, descricao, categoria, ativo e valor.
- **CSV_de_Resumo_Mensal**: Arquivo CSV com os totais mensais de receitas, despesas, investimentos e Saldo_Livre.
- **Area_de_Apoio**: Região de dados auxiliares da planilha que alimenta os gráficos.
- **Steering**: Arquivos Markdown em `.kiro/steering`. Hoje só o manual `revisar-documentacao.md`; o contexto permanente está no `AGENTS.md`.
- **Agente**: Perfil de agente de IA por papel (planejador, implementador, QA, documentação).
- **Hook**: Automação configurada em `.kiro/hooks` que reage a eventos do workspace.
- **Linha_de_Base**: Resultado de `uv sync`, `ruff check .` e `pytest` executados antes de qualquer mudança de código.
- **Roadmap**: Lista de features planejadas registrada no README.md.

## Requirements

### Requirement 1: Reorganização do workspace (concluído)

**Status:** concluído; o conteúdo já está na raiz do repositório. Mantido só para rastreabilidade.

#### Acceptance Criteria

1. THE Projeto SHALL ter `pyproject.toml`, `src/`, `tests/`, `data/`, `docs/`, `.github/`, `AGENTS.md` e `README.md` na raiz do repositório.

### Requirement 2: Instalação de ferramentas (concluído)

**Status:** concluído. Requisito original: instalar git, uv e Python 3.14 somente com confirmação separada do usuário para cada ferramenta.

#### Acceptance Criteria

1. WHEN uma ferramenta necessária não está no PATH, THE Agente SHALL pedir confirmação explícita antes de instalá-la e verificar a versão depois.

### Requirement 3: Git sem commits não solicitados (concluído)

**Status:** concluído. O versionamento passou a ser feito pelo agente principal quando o usuário autoriza (ver `AGENTS.md`, regra 2).

#### Acceptance Criteria

1. THE Agente SHALL criar commits somente quando o usuário pedir ou autorizar o versionamento, e nunca fazer push na `main`.

### Requirement 4: Linha de base do projeto (concluído)

**Status:** concluído. Antes de mudar código, `uv sync`, `uv run ruff check .` e `uv run pytest` devem estar verdes; qualquer falha é relatada ao usuário.

#### Acceptance Criteria

1. IF algum comando da Linha_de_Base falha, THEN THE Agente SHALL relatar o comando e a saída antes de implementar.

### Requirement 5: Contexto para agentes (AGENTS.md como fonte única)

**User Story:** Como desenvolvedor, quero uma única fonte de contexto para os agentes, para que não haja documentos duplicados divergindo.

#### Acceptance Criteria

1. THE `AGENTS.md` SHALL conter propósito, stack, comandos, estrutura de módulos, esquema do JSON, saídas, regras para agentes e o fluxo com IA, mantendo cerca de 100 linhas.
2. THE Projeto SHALL NOT manter steering de sempre ativo que duplique o `AGENTS.md`; o único steering é o manual `revisar-documentacao.md`.
3. THE `AGENTS.md` SHALL registrar: Decimal para dinheiro; atualização conjunta de `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` ao mudar o esquema; nomes de identificadores no padrão em português já usado; `saldo_livre = receitas - despesas - investimentos`.
4. THE `AGENTS.md` SHALL declarar a importação de extratos bancários e a interface web como fora de escopo.

### Requirement 6: Agentes por papel

**User Story:** Como desenvolvedor, quero quatro agentes por papel, para que cada tarefa seja conduzida por um perfil com responsabilidades claras.

#### Acceptance Criteria

1. THE Projeto SHALL definir quatro Agentes: planejador (spec), implementador, QA e documentação.
2. THE definição do Agente planejador SHALL limitar a atuação à criação e ao refinamento de specs, sem alterar código em `src/`.
3. THE definição do Agente implementador SHALL exigir a leitura do `AGENTS.md` e das tarefas do spec antes de alterar código, e SHALL proibir escrita em `.kiro/`, `.github/` e `AGENTS.md`.
4. THE definição do Agente QA SHALL exigir a execução de `uv run pytest` e `uv run ruff check .` e o relato dos resultados.
5. THE definição do Agente de documentação SHALL limitar a atuação a `README.md`, `AGENTS.md` e `docs/`.
6. THE definição de cada Agente SHALL registrar que não cria commits; o versionamento é do agente principal, com autorização do usuário.
7. THE definição de cada Agente SHALL registrar que valores monetários usam Decimal.

### Requirement 7: Hooks de automação

**User Story:** Como desenvolvedor, quero hooks que automatizem checagens, para que erros de estilo, regressões e documentação desatualizada sejam percebidos cedo.

#### Acceptance Criteria

1. WHEN um `.py` em `src/` ou `tests/` é salvo, THE Hook SHALL executar `scripts/checar.py` (ruff em tudo e pytest só do módulo alterado), sem sintaxe específica de shell, portável entre Windows e Linux.
2. WHEN um arquivo `loader.py`, `validador.py` ou `exemplo.json` é salvo, THE Hook SHALL exibir o lembrete de atualizar `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` em conjunto.
3. THE revisão de documentação SHALL ser acionada somente manualmente, pelo steering manual `/revisar-documentacao`.
4. THE Projeto SHALL armazenar as definições dos Hooks em `.kiro/hooks`.
5. IF a execução de `ruff` ou `pytest` por um Hook falha, THEN THE Hook SHALL exibir a saída do comando que falhou.

### Requirement 8: Validação de schema do JSON

**User Story:** Como usuário, quero que o JSON de entrada seja validado com mensagens claras, para que eu encontre e corrija erros de dados rapidamente.

#### Acceptance Criteria

1. THE Validador SHALL residir no módulo `src/controlegastos/validador.py` e SHALL operar sem dependências de terceiros novas.
2. WHEN um JSON_de_Entrada é validado, THE Validador SHALL verificar a presença do campo `anos` e, em cada ano, dos campos `ano` e `meses`.
3. WHEN um mês é validado, THE Validador SHALL verificar que `mes` é um inteiro entre 1 e 12.
4. WHEN um lançamento é validado, THE Validador SHALL verificar que `dia` é um dia válido para o mês e o ano correspondentes, incluindo 29 de fevereiro apenas em anos bissextos.
5. WHEN um lançamento ou campo monetário é validado, THE Validador SHALL verificar que `valor`, `salario` e `meta_investimento` (quando presentes) são numéricos e não booleanos.
6. WHEN um investimento é validado, THE Validador SHALL verificar que `tipo` é um Tipo_de_Investimento_Conhecido.
7. WHEN um lançamento é validado, THE Validador SHALL verificar a presença dos campos obrigatórios `descricao`, `valor` e `dia` em receitas e despesas, e `tipo`, `descricao`, `valor` e `dia` em investimentos.
8. IF o JSON_de_Entrada contém erros, THEN THE Validador SHALL reportar cada erro em português com o Caminho_do_Erro, por exemplo `anos[0].meses[2].despesas[1].valor`.
9. IF o JSON_de_Entrada contém mais de um erro, THEN THE Validador SHALL reportar todos os erros encontrados em uma única execução.
10. WHEN o Loader recebe um JSON_de_Entrada, THE Loader SHALL invocar o Validador antes de construir o LivroCaixa.
11. IF o Validador reporta ao menos um erro, THEN THE CLI SHALL exibir todas as mensagens de erro ao usuário e retornar código de saída 1.
12. WHEN o JSON_de_Entrada é válido, THE CLI SHALL manter o comportamento atual de geração e retornar código de saída 0.
13. THE Projeto SHALL aceitar como válidos os arquivos `data/entradas/exemplo.json` e `data/entradas/exemplo-completo.json`.
14. WHEN o esquema de dados é alterado, THE Agente SHALL atualizar `loader.py`, `validador.py`, `exemplo.json` e `AGENTS.md` na mesma mudança.
15. THE suíte de testes SHALL conter testes do Validador para cada regra dos critérios 2 a 7, cobrindo ao menos um caso válido e um inválido por regra.

### Requirement 9: Exportação CSV

**User Story:** Como usuário, quero exportar os dados em CSV, para que eu possa abrir os lançamentos e o resumo em outras ferramentas.

#### Acceptance Criteria

1. THE CLI SHALL oferecer no subcomando `gerar` a opção `--formato` com os valores `xlsx`, `csv` e `ambos`.
2. WHEN a opção `--formato` não é informada, THE CLI SHALL gerar somente o arquivo .xlsx, mantendo o comportamento atual.
3. WHEN `--formato` é `csv` ou `ambos`, THE Exportador_CSV SHALL gerar o CSV_de_Lancamentos com as colunas `data`, `tipo`, `descricao`, `categoria`, `ativo` e `valor`.
4. WHEN `--formato` é `csv` ou `ambos`, THE Exportador_CSV SHALL gerar o CSV_de_Resumo_Mensal com os totais mensais de receitas, despesas, investimentos e Saldo_Livre.
5. THE Exportador_CSV SHALL escrever cada valor monetário a partir de Decimal, usando ponto como separador decimal e duas casas decimais.
6. THE Exportador_CSV SHALL gravar os arquivos CSV com codificação UTF-8.
7. WHEN o Exportador_CSV escreve a coluna `data`, THE Exportador_CSV SHALL usar o formato `AAAA-MM-DD`.
8. WHEN o Exportador_CSV escreve a coluna `tipo`, THE Exportador_CSV SHALL usar os valores `receita`, `despesa` ou `investimento`.
9. THE Exportador_CSV SHALL calcular o Saldo_Livre do CSV_de_Resumo_Mensal igual ao valor exibido no Resumo Geral do .xlsx para o mesmo mês.
10. IF o diretório de destino do CSV não existe, THEN THE Exportador_CSV SHALL criar o diretório antes de gravar os arquivos.
11. IF `--formato` recebe um valor fora de `xlsx`, `csv` e `ambos`, THEN THE CLI SHALL exibir mensagem de erro em português e retornar código de saída diferente de 0.
12. WHEN `--formato` é `ambos`, THE CLI SHALL informar o caminho de cada arquivo gerado.
13. THE suíte de testes SHALL conter testes do Exportador_CSV que verifiquem cabeçalhos, formato decimal, codificação e consistência dos totais com o Gerador.

### Requirement 10: Interface web (ADIADO, fora desta fase)

**Status:** descartado nesta fase (decisão do usuário: sem Streamlit). Será avaliado em outro PR, se houver interesse. Os critérios originais foram removidos; as propriedades 7 a 9 do design ficam suspensas.

### Requirement 11: Gráficos extras

**User Story:** Como usuário, quero gráficos extras na planilha, para que eu acompanhe a evolução do patrimônio, as maiores despesas e a comparação entre meses.

#### Acceptance Criteria

1. WHEN o Gerador produz a aba Gráficos, THE Gerador SHALL incluir um gráfico de evolução do patrimônio baseado no acumulado mensal de investimentos.
2. WHEN o Gerador produz a aba Gráficos, THE Gerador SHALL incluir um gráfico de ranking das categorias de despesa em ordem decrescente de valor total.
3. WHEN o Gerador produz a aba Gráficos, THE Gerador SHALL incluir um gráfico de comparativo entre meses.
4. THE Gerador SHALL alimentar os novos gráficos a partir da Area_de_Apoio existente, estendendo-a com os dados necessários.
5. THE Gerador SHALL criar os novos gráficos com openpyxl, sem dependências novas.
6. WHILE o JSON_de_Entrada não contém despesas com categoria, THE Gerador SHALL agrupar as despesas sem categoria sob o rótulo `Sem categoria` no ranking.
7. IF o JSON_de_Entrada não contém dados suficientes para um gráfico, THEN THE Gerador SHALL gerar a aba Gráficos sem esse gráfico e sem lançar erro.
8. THE Gerador SHALL manter os gráficos existentes de pizza por classe de investimento e de barras mensais.
9. THE suíte de testes SHALL verificar que a aba Gráficos contém os três novos gráficos para uma entrada com dados completos.
10. THE Projeto SHALL atualizar as imagens em `docs/media` usando somente dados fictícios.

### Requirement 12: Fechamento da fase

**User Story:** Como mantenedor, quero fechar a fase com documentação, CI e verificação ponta a ponta, para que o projeto fique consistente e confiável.

#### Acceptance Criteria

1. WHEN as features são concluídas, THE Agente SHALL atualizar `README.md` e `AGENTS.md` com os novos módulos, opções e dependências.
2. WHEN uma feature do Roadmap é concluída, THE Agente SHALL marcar essa feature como concluída no Roadmap do `README.md`.
3. THE workflow de CI em `.github/workflows/ci.yml` SHALL instalar as dependências com `uv sync` (não há dependências opcionais).
4. THE workflow de CI SHALL executar `ruff` e `pytest` cobrindo os módulos novos.
5. WHEN o fechamento é executado, THE Agente SHALL rodar a suíte completa com `uv run pytest` e `uv run ruff check .` e relatar o resultado.
6. WHEN o fechamento é executado, THE Agente SHALL executar uma geração ponta a ponta de `data/entradas/exemplo-completo.json` com `--formato ambos` e verificar a existência do .xlsx e dos dois CSV.
7. IF a suíte ou a geração ponta a ponta falha, THEN THE Agente SHALL relatar a falha ao usuário e manter o Roadmap sem marcar as features afetadas.
8. THE documentação SHALL registrar a importação de extratos bancários como fora de escopo desta fase.
