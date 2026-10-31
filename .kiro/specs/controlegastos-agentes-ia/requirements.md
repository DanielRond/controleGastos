# Requirements Document

## Introduction

Este documento define os requisitos para organizar o projeto controleGastos para desenvolvimento assistido por agentes de IA no Kiro e para evoluí-lo com as features do roadmap. O controleGastos é uma CLI Python (>= 3.14, gerenciada com uv, usando openpyxl, pytest e ruff) que gera planilhas .xlsx de gastos pessoais a partir de arquivos JSON.

O escopo desta fase cobre: (1) preparação do ambiente e da raiz do workspace; (2) organização para IA (steering, agentes e hooks); (3) validação de schema do JSON; (4) exportação CSV; (5) interface web; (6) gráficos extras; (7) fechamento (documentação, CI e verificação ponta a ponta).

A importação de extratos bancários está FORA do escopo desta fase. Neste momento, apenas specs e documentação são produzidos; nenhum código é implementado. Os requisitos abaixo descrevem o comportamento esperado para as tarefas de implementação futuras.

Prioridade das features: (A) validação de schema, (B) exportação CSV, (C) interface web, (E) gráficos extras.

## Glossary

- **Projeto**: O repositório controleGastos, cujo conteúdo é movido da pasta controleGastos-main para a raiz do workspace.
- **CLI**: A interface de linha de comando `controlegastos`, implementada em `cli.py` com argparse.
- **Loader**: O módulo `loader.py`, que converte o JSON em objetos `LivroCaixa`.
- **Modelo**: O módulo `modelo.py`, com as dataclasses Receita, Despesa, Investimento, Mes, Ano e LivroCaixa, que usam Decimal para valores monetários.
- **Gerador**: O módulo `generator.py`, que produz o arquivo .xlsx (Resumo Geral, abas por mês e Gráficos).
- **Validador**: O novo módulo `validador.py`, que verifica o schema do JSON de entrada.
- **Exportador_CSV**: O novo módulo responsável por gerar os arquivos CSV.
- **Interface_Web**: A interface web iniciada pelo subcomando `controlegastos ui`.
- **Servico_Core**: A camada de lógica (carregar, validar, gerar, exportar) usada pela Interface_Web e separada da camada de apresentação.
- **JSON_de_Entrada**: Arquivo JSON com lançamentos, seguindo o esquema documentado no AGENTS.md.
- **Caminho_do_Erro**: Texto que indica a posição do campo inválido no JSON, no formato `anos[0].meses[2].despesas[1].valor`.
- **Tipo_de_Investimento_Conhecido**: Um dos valores `renda_fixa`, `fii` ou `cripto`.
- **Saldo_Livre**: Valor calculado como receitas menos despesas menos investimentos.
- **CSV_de_Lancamentos**: Arquivo CSV com as colunas data, tipo, descricao, categoria, ativo e valor.
- **CSV_de_Resumo_Mensal**: Arquivo CSV com os totais mensais de receitas, despesas, investimentos e Saldo_Livre.
- **Area_de_Apoio**: Região de dados auxiliares da planilha que alimenta os gráficos.
- **Steering**: Arquivos Markdown em `.kiro/steering` que dão contexto permanente aos agentes.
- **Agente**: Perfil de agente de IA por papel (planejador, implementador, QA, documentação).
- **Hook**: Automação configurada em `.kiro/hooks` que reage a eventos do workspace.
- **Linha_de_Base**: Resultado de `uv sync`, `ruff check .` e `pytest` executados antes de qualquer mudança de código.
- **Roadmap**: Lista de features planejadas registrada no README.md.

## Requirements

### Requirement 1: Reorganização do workspace

**User Story:** Como desenvolvedor, quero mover o conteúdo de controleGastos-main para a raiz do workspace, para que o Kiro enxergue o Projeto na raiz e os caminhos de steering, hooks e specs funcionem.

#### Acceptance Criteria

1. WHEN a reorganização do workspace é executada, THE Projeto SHALL ter `pyproject.toml`, `src/`, `tests/`, `data/`, `docs/`, `.github/`, `AGENTS.md` e `README.md` na raiz do workspace.
2. WHEN a reorganização do workspace é concluída, THE Projeto SHALL preservar o conteúdo byte a byte de todos os arquivos movidos.
3. WHEN a reorganização do workspace é concluída, THE Projeto SHALL remover a pasta `controleGastos-main` vazia da raiz do workspace.
4. IF existir um arquivo na raiz do workspace com o mesmo nome de um arquivo a ser movido, THEN THE Projeto SHALL interromper a movimentação e informar o conflito ao usuário.
5. THE Projeto SHALL preservar a pasta `.kiro/specs` existente durante a reorganização.

### Requirement 2: Instalação de ferramentas com confirmação

**User Story:** Como desenvolvedor, quero instalar as ferramentas necessárias com minha confirmação, para que eu mantenha controle sobre o que é instalado na minha máquina.

#### Acceptance Criteria

1. WHEN uma ferramenta entre git, uv e Python 3.14 não está disponível no PATH, THE Agente SHALL solicitar a confirmação explícita do usuário antes de instalar essa ferramenta via winget.
2. THE Agente SHALL solicitar uma confirmação separada para cada ferramenta a ser instalada.
3. IF o usuário não confirma a instalação de uma ferramenta, THEN THE Agente SHALL registrar a ferramenta como pendente e prosseguir somente com as etapas que não dependem dela.
4. WHEN uma ferramenta já está disponível no PATH, THE Agente SHALL pular a instalação dessa ferramenta.
5. WHEN a instalação de uma ferramenta termina, THE Agente SHALL verificar a versão instalada executando o comando de versão da ferramenta.

### Requirement 3: Inicialização do git sem commits

**User Story:** Como desenvolvedor, quero inicializar ou ligar o repositório git sem criar commits, para que eu decida quando versionar as mudanças.

#### Acceptance Criteria

1. WHEN o workspace não contém um repositório git, THE Agente SHALL inicializar um repositório git na raiz do workspace.
2. WHEN o usuário informa uma URL de repositório remoto, THE Agente SHALL configurar essa URL como remoto `origin`.
3. THE Agente SHALL manter o histórico do repositório sem novos commits criados durante esta fase, exceto mediante pedido explícito do usuário.
4. WHEN o repositório git é inicializado ou ligado, THE Agente SHALL confirmar que o `.gitignore` do Projeto está presente na raiz.

### Requirement 4: Linha de base do projeto

**User Story:** Como desenvolvedor, quero uma linha de base verde antes de mudar o código, para que eu possa distinguir problemas pré-existentes de regressões.

#### Acceptance Criteria

1. WHEN as ferramentas necessárias estão instaladas, THE Agente SHALL executar `uv sync`, `uv run ruff check .` e `uv run pytest` na raiz do workspace, nessa ordem.
2. WHEN a Linha_de_Base é executada, THE Agente SHALL registrar o resultado de cada comando (sucesso ou falha e quantidade de testes aprovados e reprovados).
3. IF algum comando da Linha_de_Base falha, THEN THE Agente SHALL relatar o comando que falhou e a saída de erro ao usuário antes de iniciar qualquer implementação.

### Requirement 5: Steering do projeto

**User Story:** Como desenvolvedor, quero arquivos de steering do projeto, para que os agentes de IA tenham contexto consistente sobre produto, tecnologia, estrutura e convenções.

#### Acceptance Criteria

1. THE Projeto SHALL conter os arquivos `.kiro/steering/produto.md`, `.kiro/steering/tech.md`, `.kiro/steering/estrutura.md` e `.kiro/steering/convencoes.md`.
2. THE arquivo `produto.md` SHALL descrever o propósito do Projeto, o público-alvo, a saída em .xlsx com CSV e interface web como complementos, e o roadmap com a ordem de prioridade A, B, C, E.
3. THE arquivo `tech.md` SHALL listar Python >= 3.14, uv, openpyxl, pytest, ruff e os comandos `uv sync`, `uv run pytest` e `uv run ruff check .`.
4. THE arquivo `estrutura.md` SHALL descrever as responsabilidades dos módulos `cli.py`, `loader.py`, `modelo.py` e `generator.py`, e dos diretórios `tests/`, `data/entradas/`, `docs/media/` e `saida/`.
5. THE arquivo `convencoes.md` SHALL registrar as regras: valores monetários em Decimal, nenhum commit sem pedido explícito, atualização conjunta de `loader.py`, `exemplo.json` e `AGENTS.md` ao mudar o esquema, código em inglês, e documentação e mensagens ao usuário em português.
6. THE arquivo `convencoes.md` SHALL registrar a convenção Saldo_Livre igual a receitas menos despesas menos investimentos.
7. THE arquivo `produto.md` SHALL declarar a importação de extratos bancários como fora do escopo desta fase.
8. WHEN o conteúdo de um arquivo de steering contradiz o AGENTS.md, THE Agente SHALL tratar o AGENTS.md como fonte de verdade e corrigir o arquivo de steering.

### Requirement 6: Agentes por papel

**User Story:** Como desenvolvedor, quero quatro agentes por papel, para que cada tarefa seja conduzida por um perfil com responsabilidades claras.

#### Acceptance Criteria

1. THE Projeto SHALL definir quatro Agentes: planejador (spec), implementador, QA e documentação.
2. THE definição do Agente planejador SHALL limitar a atuação à criação e ao refinamento de specs, sem alterar código em `src/`.
3. THE definição do Agente implementador SHALL exigir a leitura dos arquivos de Steering e das tarefas do spec antes de alterar código.
4. THE definição do Agente QA SHALL exigir a execução de `uv run pytest` e `uv run ruff check .` e o relato dos resultados.
5. THE definição do Agente de documentação SHALL limitar a atuação a `README.md`, `AGENTS.md`, `docs/` e arquivos de Steering.
6. THE definição de cada Agente SHALL registrar a regra de nunca criar commits sem pedido explícito do usuário.
7. THE definição de cada Agente SHALL registrar que valores monetários usam Decimal.

### Requirement 7: Hooks de automação

**User Story:** Como desenvolvedor, quero hooks que automatizem checagens, para que erros de estilo, regressões e documentação desatualizada sejam percebidos cedo.

#### Acceptance Criteria

1. WHEN um arquivo em `src/` ou `tests/` é salvo, THE Hook SHALL executar `uv run ruff check .` e `uv run pytest`.
2. WHEN um arquivo `loader.py`, `validador.py` ou `exemplo.json` é salvo, THE Hook SHALL exibir o lembrete de atualizar `loader.py`, `exemplo.json` e `AGENTS.md` em conjunto.
3. WHERE a revisão de documentação está habilitada, THE Hook SHALL iniciar a revisão de documentação somente mediante acionamento manual pelo usuário.
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

### Requirement 10: Interface web

**User Story:** Como usuário, quero uma interface web simples, para que eu registre lançamentos e gere planilhas sem editar JSON manualmente.

#### Acceptance Criteria

1. THE CLI SHALL oferecer o subcomando `controlegastos ui` que inicia a Interface_Web.
2. THE Projeto SHALL declarar a dependência da Interface_Web como dependência opcional no `pyproject.toml`, sem impacto na instalação padrão da CLI.
3. THE documento de design SHALL registrar a escolha do framework da Interface_Web, com Streamlit como sugestão inicial.
4. IF o usuário executa `controlegastos ui` sem a dependência opcional instalada, THEN THE CLI SHALL exibir mensagem em português com o comando para instalá-la e retornar código de saída diferente de 0.
5. WHEN o usuário envia um arquivo JSON na Interface_Web, THE Interface_Web SHALL carregar os lançamentos por meio do Servico_Core.
6. WHEN o usuário preenche o formulário de novo lançamento e confirma, THE Interface_Web SHALL adicionar o lançamento à sessão atual.
7. WHEN dados são carregados ou enviados pelo formulário, THE Interface_Web SHALL validá-los com o Validador e exibir cada erro com seu Caminho_do_Erro.
8. WHEN o usuário solicita salvar, THE Interface_Web SHALL gravar o JSON válido em `data/entradas/`.
9. IF os dados contêm erros de validação, THEN THE Interface_Web SHALL impedir o salvamento e a geração de arquivos.
10. WHEN o usuário solicita gerar, THE Interface_Web SHALL oferecer o download do .xlsx e dos arquivos CSV.
11. THE Servico_Core SHALL conter toda a lógica de carregar, validar, salvar, gerar e exportar, sem importar o framework da Interface_Web.
12. THE suíte de testes SHALL cobrir o Servico_Core sem necessidade de iniciar a Interface_Web.
13. IF o arquivo enviado não é um JSON legível, THEN THE Interface_Web SHALL exibir mensagem de erro em português e manter os dados anteriores da sessão.

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

1. WHEN as features são concluídas, THE Agente SHALL atualizar `README.md` e `AGENTS.md` com os novos módulos, subcomandos, opções e dependências.
2. WHEN uma feature do Roadmap é concluída, THE Agente SHALL marcar essa feature como concluída no Roadmap do `README.md`.
3. THE workflow de CI em `.github/workflows/ci.yml` SHALL instalar as dependências opcionais necessárias aos testes dos novos módulos.
4. THE workflow de CI SHALL executar `ruff` e `pytest` cobrindo os módulos novos.
5. WHEN o fechamento é executado, THE Agente SHALL rodar a suíte completa com `uv run pytest` e `uv run ruff check .` e relatar o resultado.
6. WHEN o fechamento é executado, THE Agente SHALL executar uma geração ponta a ponta de `data/entradas/exemplo-completo.json` com `--formato ambos` e verificar a existência do .xlsx e dos dois CSV.
7. IF a suíte ou a geração ponta a ponta falha, THEN THE Agente SHALL relatar a falha ao usuário e manter o Roadmap sem marcar as features afetadas.
8. THE documentação SHALL registrar a importação de extratos bancários como fora de escopo desta fase.
