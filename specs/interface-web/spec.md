---
capacidade: interface-web
codigo: WEB
status: rascunho
---

# Capacidade: interface web (rascunho)

## Objetivo

O objetivo real do projeto: usar o controle de gastos de forma prática, sem editar JSON à mão. A CLI foi o primeiro passo e não é o produto final. Este documento guarda a intenção e as decisões já tomadas; **não tem requisitos fechados nem IDs**, então o CI não cobra testes dele.

## Decisões já tomadas

- Streamlit foi descartado (decisão do usuário).
- O núcleo (carregar, validar, calcular, gerar) não pode depender da CLI nem de um framework de UI; a CLI e a web devem chamar as mesmas funções.

## Já preparado no código

- `carregar_dados(dados)` valida e constrói a partir de um `dict`, sem arquivo (serve a um formulário ou upload).
- `validar` devolve `ErroDeValidacao(caminho, mensagem)`, pronto para virar tabela de erros.
- Totais e gráficos vêm do modelo em `Decimal`.

## Lacunas conhecidas (a resolver antes de implementar)

- Geração em memória: `gerar_planilha` e `exportar_csv` recebem caminho; a web precisa de bytes para download.
- Dados dos gráficos hoje são funções privadas do `generator.py`.
- A CLI orquestra o fluxo (carregar, gerar, mensagens); isso deve virar uma camada de serviço reutilizável.

## Perguntas abertas

1. Onde vivem os dados: arquivos JSON locais (versionáveis), ou banco (ex.: SQLite)? Quem usa: só você, na sua máquina, ou várias pessoas/hospedado?
2. Framework: opções a avaliar (FastAPI + HTMX/Jinja, Flask, NiceGUI, Django). Critérios: simplicidade, compatibilidade com Python 3.14, facilidade de agentes de IA manterem.
3. Funcionalidades mínimas da primeira versão: registrar lançamento, listar/editar/excluir, ver resumo e gráficos, baixar `.xlsx`/CSV?
4. Autenticação (se for acessado fora da máquina local).
5. Importação de extratos bancários entra antes ou depois da interface?

## Próximo passo

Responder as perguntas acima, definir os requisitos (`WEB-01...`), mudar o `status` para `vigente` e só então criar `design.md` e `tasks.md` nesta pasta.
