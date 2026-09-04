"""Carregamento de dados a partir de arquivos JSON.

Formato esperado (data/entradas/exemplo.json):

{
  "moeda": "BRL",
  "anos": [
    {
      "ano": 2025,
      "meses": [
        {
          "mes": 1,
          "salario": 5000.00,
          "outras_receitas": 250.00,
          "despesas": [
            {"descricao": "Aluguel", "valor": 1200.00, "dia": 5, "categoria": "moradia"}
          ],
          "investimentos": [
            {"tipo": "renda_fixa", "valor": 1000.00, "dia": 10, "descricao": "CDB"}
          ]
        }
      ]
    }
  ]
}
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from .modelo import Despesa, Investimento, LivroCaixa, Receita


def _dia_para_data(ancora: date, dia: int) -> date:
    return date(ancora.year, ancora.month, dia)


def _link(ancora: date, item: dict) -> tuple[str, Decimal, date, str]:
    descricao = item.get("descricao", "")
    valor = Decimal(str(item["valor"]))
    dia = int(item.get("dia", 1))
    categoria = item.get("categoria", "geral")
    return descricao, valor, _dia_para_data(ancora, dia), categoria


def carregar_json(caminho: str | Path) -> LivroCaixa:
    caminho = Path(caminho)
    dados = json.loads(caminho.read_text(encoding="utf-8"))

    livros = LivroCaixa(moeda=dados.get("moeda", "BRL"))

    for ano_dados in dados.get("anos", []):
        numero_ano = int(ano_dados["ano"])
        ano = livros.ano(numero_ano)
        for mes_dados in ano_dados.get("meses", []):
            numero_mes = int(mes_dados["mes"])
            atual = ano.mes(numero_mes)
            ancora = date(numero_ano, numero_mes, 1)

            salario = Decimal(str(mes_dados.get("salario", "0")))
            if salario:
                atual.receitas.append(Receita("Salário", salario, ancora, "salario"))
            for extra in mes_dados.get("receitas", []):
                descricao, valor, quando, categoria = _link(ancora, extra)
                atual.receitas.append(Receita(descricao, valor, quando, categoria))

            for item in mes_dados.get("despesas", []):
                descricao, valor, quando, categoria = _link(ancora, item)
                atual.despesas.append(Despesa(descricao, valor, quando, categoria))

            for item in mes_dados.get("investimentos", []):
                tipo = item.get("tipo", "")
                descricao, valor, quando, categoria = _link(ancora, item)
                atual.investimentos.append(
                    Investimento(descricao, valor, quando, categoria, tipo=tipo)
                )

    return livros