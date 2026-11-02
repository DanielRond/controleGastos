"""Testes do carregamento de dados (loader.py)."""

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

from controlegastos.loader import carregar_dados, carregar_json

RAIZ = Path(__file__).resolve().parent.parent
EXEMPLO = RAIZ / "data" / "entradas" / "exemplo.json"


# Spec: LAN-01, LAN-02, LAN-03
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


# Spec: LAN-05
def test_carrega_exemplo_meta_investimento() -> None:
    livros = carregar_json(EXEMPLO)
    assert livros.ano(2025).mes(1).meta_investimento == Decimal("1000.00")


# Spec: LAN-04
def test_lancamento_em_dia_especifico() -> None:
    livros = carregar_json(EXEMPLO)
    mes = livros.ano(2025).mes(1)
    aluguel = next(d for d in mes.despesas if d.descricao == "Aluguel")
    assert aluguel.data == date(2025, 1, 5)
    assert aluguel.valor == Decimal("1200.00")


# Spec: LAN-05
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


# Spec: VAL-10
def test_erro_de_validacao_traz_todos_os_erros() -> None:
    import pytest

    from controlegastos.loader import ErroDeValidacaoJSON, carregar_dados

    dados = {
        "anos": [
            {
                "ano": 2025,
                "meses": [
                    {
                        "mes": 13,
                        "despesas": [{"descricao": "x", "valor": "abc", "dia": 1}],
                    },
                    {"mes": 1, "salario": True},
                ],
            }
        ]
    }
    with pytest.raises(ErroDeValidacaoJSON) as info:
        carregar_dados(dados)

    caminhos = {e.caminho for e in info.value.erros}
    assert "anos[0].meses[0].mes" in caminhos
    assert "anos[0].meses[0].despesas[0].valor" in caminhos
    assert "anos[0].meses[1].salario" in caminhos
    assert isinstance(info.value, ValueError)


# Spec: VAL-10
def test_json_ilegivel_gera_mensagem_em_portugues(tmp_path: Path) -> None:
    import pytest

    arquivo = tmp_path / "quebrado.json"
    arquivo.write_text("{ nao e json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON inválido na linha 1"):
        carregar_json(arquivo)


# Spec: LAN-01, LAN-04
def test_salario_vira_receita_no_dia_1_e_categoria_padrao_e_geral() -> None:
    dados = {
        "anos": [{"ano": 2025, "meses": [{"mes": 3, "salario": 100, "despesas": [{"descricao": "x", "valor": 5, "dia": 2}]}]}]
    }
    mes = carregar_dados(dados).ano(2025).mes(3)

    salario = mes.receitas[0]
    assert (salario.descricao, salario.categoria, salario.data) == ("Salário", "salario", date(2025, 3, 1))
    assert salario.valor == Decimal(100)
    assert mes.despesas[0].categoria == "geral"
    assert mes.despesas[0].data == date(2025, 3, 2)

