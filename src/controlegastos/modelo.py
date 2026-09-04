"""Modelos de dados do controle de gastos.

Organização por ano e mês, com três tipos de lançamentos:
- Receita (o que recebi)
- Despesa (o que gastei)
- Investimento (onde apliquei)

Todos os valores monetários usam Decimal para evitar erros de ponto flutuante.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(slots=True)
class Transacao:
    descricao: str
    valor: Decimal
    data: date
    categoria: str


@dataclass(slots=True)
class Receita(Transacao):
    pass


@dataclass(slots=True)
class Despesa(Transacao):
    pass


@dataclass(slots=True)
class Investimento(Transacao):
    tipo: str = ""


@dataclass(slots=True)
class Mes:
    numero: int
    ano: int
    receitas: list[Receita] = field(default_factory=list)
    despesas: list[Despesa] = field(default_factory=list)
    investimentos: list[Investimento] = field(default_factory=list)

    @property
    def total_receitas(self) -> Decimal:
        return sum((t.valor for t in self.receitas), Decimal(0))

    @property
    def total_despesas(self) -> Decimal:
        return sum((t.valor for t in self.despesas), Decimal(0))

    @property
    def total_investimentos(self) -> Decimal:
        return sum((t.valor for t in self.investimentos), Decimal(0))

    @property
    def saldo_livre(self) -> Decimal:
        return self.total_receitas - self.total_despesas - self.total_investimentos


@dataclass(slots=True)
class Ano:
    numero: int
    meses: dict[int, Mes] = field(default_factory=dict)

    def mes(self, numero: int) -> Mes:
        if numero not in self.meses:
            self.meses[numero] = Mes(numero=numero, ano=self.numero)
        return self.meses[numero]

    @property
    def total_receitas(self) -> Decimal:
        return sum((m.total_receitas for m in self.meses.values()), Decimal(0))

    @property
    def total_despesas(self) -> Decimal:
        return sum((m.total_despesas for m in self.meses.values()), Decimal(0))

    @property
    def total_investimentos(self) -> Decimal:
        return sum((m.total_investimentos for m in self.meses.values()), Decimal(0))


@dataclass(slots=True)
class LivroCaixa:
    moeda: str = "BRL"
    anos: dict[int, Ano] = field(default_factory=dict)

    def ano(self, numero: int) -> Ano:
        if numero not in self.anos:
            self.anos[numero] = Ano(numero=numero)
        return self.anos[numero]