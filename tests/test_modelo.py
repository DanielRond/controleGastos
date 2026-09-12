"""Testes dos modelos de dados (modelo.py)."""

from datetime import date
from decimal import Decimal

from controlegastos.modelo import Ano, Despesa, Investimento, LivroCaixa, Mes, Receita


def _mes() -> Mes:
    return Mes(
        numero=5,
        ano=2025,
        receitas=[Receita("Salário", Decimal("3000.00"), date(2025, 5, 5), "salario")],
        despesas=[Despesa("Aluguel", Decimal("1000.00"), date(2025, 5, 5), "moradia")],
        investimentos=[
            Investimento("CDI", Decimal("500.00"), date(2025, 5, 5), "reserva", tipo="renda_fixa")
        ],
        meta_investimento=Decimal("600.00"),
    )


def test_mes_totais() -> None:
    mes = _mes()
    assert mes.total_receitas == Decimal("3000.00")
    assert mes.total_despesas == Decimal("1000.00")
    assert mes.total_investimentos == Decimal("500.00")
    assert mes.saldo_livre == Decimal("1500.00")


def test_mes_vazio() -> None:
    mes = Mes(numero=1, ano=2025)
    assert mes.total_receitas == Decimal(0)
    assert mes.total_despesas == Decimal(0)
    assert mes.total_investimentos == Decimal(0)
    assert mes.saldo_livre == Decimal(0)


def test_ano_totais_somam_meses() -> None:
    jan = Mes(numero=1, ano=2025)
    jan.receitas.append(Receita("Salário", Decimal("1000.00"), date(2025, 1, 1), "salario"))
    fev = Mes(numero=2, ano=2025)
    fev.despesas.append(Despesa("Conta", Decimal("200.00"), date(2025, 2, 1), "geral"))

    ano = Ano(numero=2025)
    ano.meses[1] = jan
    ano.meses[2] = fev

    assert ano.total_receitas == Decimal("1000.00")
    assert ano.total_despesas == Decimal("200.00")
    assert ano.total_investimentos == Decimal(0)


def test_ano_mes_cria_quando_ausente() -> None:
    ano = Ano(numero=2025)
    mes = ano.mes(7)
    assert mes.numero == 7
    assert mes.ano == 2025
    assert ano.mes(7) is mes


def test_livro_caixa_ano_cria_quando_ausente() -> None:
    livros = LivroCaixa()
    ano = livros.ano(2030)
    assert ano.numero == 2030
    assert livros.ano(2030) is ano