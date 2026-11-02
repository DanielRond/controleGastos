---
capacidade: validacao
codigo: VAL
status: vigente
---

# Capacidade: validação do JSON de entrada

## Objetivo

Rejeitar entradas inválidas **antes** de qualquer geração, mostrando todos os problemas de uma vez, com o caminho exato de cada campo, para que o usuário corrija rápido.

## Comportamento

- **VAL-01** O documento deve ser um objeto JSON com `anos` presente e do tipo lista. Raiz que não é objeto gera um único erro com caminho `(raiz)`.
- **VAL-02** Cada ano deve ter `ano` inteiro (não booleano) entre 1 e 9999 e `meses` do tipo lista.
- **VAL-03** Cada mês deve ter `mes` inteiro entre 1 e 12. Mês inválido não gera erros em cascata nos seus lançamentos.
- **VAL-04** `dia` deve ser inteiro e válido para o mês e o ano; 29/02 só em ano bissexto.
- **VAL-05** `valor`, `salario` e `meta_investimento` (quando presentes) são números finitos, não booleanos; strings numéricas como `"10.5"` são rejeitadas.
- **VAL-06** `tipo` de investimento deve ser `renda_fixa`, `fii` ou `cripto`; a mensagem lista os valores aceitos.
- **VAL-07** Obrigatórios por lançamento: `descricao`, `valor`, `dia`; em investimentos, também `tipo`.
- **VAL-08** `receitas`, `despesas` e `investimentos`, se presentes, são listas de objetos; `descricao`, `categoria` e `ativo` (quando presentes) são texto.
- **VAL-09** Todos os erros são reportados em uma única execução, em português, com o caminho no formato `anos[0].meses[2].despesas[1].valor` (índices base 0). A validação nunca lança por causa do conteúdo e não altera a entrada.
- **VAL-10** O loader valida antes de construir o `LivroCaixa`; com erros, levanta `ErroDeValidacaoJSON` (subclasse de `ValueError`) com todos eles. JSON ilegível gera mensagem em português com linha e coluna.
- **VAL-11** Na CLI, com erros: exibe cada erro, retorna código 1 e **não grava nenhum arquivo**. Dado um JSON válido, Quando gerar, Então retorna 0.
- **VAL-12** `data/entradas/exemplo.json` e `exemplo-completo.json` são sempre válidos.
- **VAL-13** `valor`, `salario` e `meta_investimento` têm no máximo duas casas decimais; mais que isso é erro no caminho do campo (`valor deve ter no máximo 2 casas decimais`), nunca é arredondado em silêncio. Vale também para a CLI.

## Exemplo

Entrada com mês 13, despesa sem `dia` e `valor` texto produz:

```text
anos[0].meses[0].mes: mes deve ser um inteiro entre 1 e 12
anos[0].meses[0].despesas[0].dia: campo obrigatório 'dia' ausente
anos[0].meses[0].despesas[0].valor: valor deve ser numérico finito (não booleano)
```

## Fora de escopo

- Validação semântica (ex.: despesa duplicada, valores negativos, meses repetidos).
- Correção automática do arquivo.

## Perguntas abertas

- Valores negativos devem ser erro? Hoje são aceitos.
- A interface web mostrará esses erros por campo (`caminho`, `mensagem`); o contrato de `ErroDeValidacao` deve se manter estável.


## Rastreabilidade

`validador.py`, `loader.py`, `cli.py`; testes `test_validador*.py`, `test_loader.py`, `test_cli*.py`.
