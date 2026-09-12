"""Testes do carregamento de dados (loader.py)."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from controlegastos.loader import carregar_json

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


def test_carrega_exemplo_com_totais_decimal() -> None:
    livros = carregar_json(EXEMPLO)

    mes = livros.ano(2025).mes(1)
    assert mes.total_receitas == Decimal("5250.00")
    assert mes.total_despesas == Decimal("1780.00")
    assert mes.total_investimentos == Decimal("1000.00")
    assert mes.saldo_livre == Decimal("2470.00")

    for valor in (
        mes.total_receitas,
        mes.total_despesas,
        mes.total_investimentos,
        mes.saldo_livre,
    ):
        assert isinstance(valor, Decimal), "valores monetários devem ser Decimal"


def test_carrega_exemplo_meta_investimento() -> None:
    livros = carregar_json(EXEMPLO)
    assert livros.ano(2025).mes(1).meta_investimento == Decimal("1000.00")


def test_lancamento_em_dia_especifico() -> None:
    livros = carregar_json(EXEMPLO)
    mes = livros.ano(2025).mes(1)
    aluguel = next(d for d in mes.despesas if d.descricao == "Aluguel")
    assert aluguel.data == date(2025, 1, 5)
    assert aluguel.valor == Decimal("1200.00")


def test_mes_sem_salario_e_meta(tmp_path: Path) -> None:
    dados = {
        "moeda": "BRL",
        "anos": [
            {
                "ano": 2025,
                "meses": [
                    {
                        "mes": 3,
                        "despesas": [
                            {"descricao": "Internet", "valor": 100.00, "dia": 2, "categoria": "utilidades"}
                        ],
                    }
                ],
            }
        ],
    }
    arquivo = tmp_path / "sem-salario.json"
    arquivo.write_text(json.dumps(dados, ensure_ascii=False), encoding="utf-8")

    livros = carregar_json(arquivo)
    mes = livros.ano(2025).mes(3)
    assert mes.total_receitas == Decimal(0)
    assert mes.meta_investimento == Decimal(0)
    assert mes.total_despesas == Decimal("100.00")