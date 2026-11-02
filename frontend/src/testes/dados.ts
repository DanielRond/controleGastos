import type { Lancamento, MesSaida } from "../api/tipos";

export const lanc = (extra: Partial<Lancamento> = {}): Lancamento => ({
  id: 1,
  ano: 2026,
  mes: 11,
  tipo: "despesa",
  descricao: "Mercado",
  valor: "100.50",
  dia: 3,
  categoria: "alimentacao",
  tipo_investimento: null,
  ativo: null,
  origem: "manual",
  apagado_em: null,
  ...extra,
});

export const mesVazio = (extra: Partial<MesSaida> = {}): MesSaida => ({
  ano: 2026,
  mes: 11,
  salario: null,
  meta_investimento: null,
  lancamentos: [],
  totais: { receitas: "0.00", despesas: "0.00", investimentos: "0.00", saldo_livre: "0.00" },
  investimentos_por_classe: [],
  meta: null,
  ...extra,
});

export const mesComDados = (): MesSaida =>
  mesVazio({
    salario: "3000.00",
    meta_investimento: "850.00",
    lancamentos: [
      lanc({ id: 1, dia: 3, descricao: "Mercado", valor: "100.50" }),
      lanc({ id: 2, dia: 5, tipo: "receita", descricao: "Freela", valor: "200.00", categoria: "extra" }),
      lanc({ id: 3, dia: 10, tipo: "investimento", descricao: "Aporte FII", valor: "300.00", categoria: "geral", tipo_investimento: "fii", ativo: "KNSC11" }),
    ],
    totais: { receitas: "3200.00", despesas: "100.50", investimentos: "300.00", saldo_livre: "2799.50" },
    investimentos_por_classe: [{ tipo: "fii", total: "300.00", percentual: "100.00" }],
    meta: { valor: "850.00", investido: "300.00", diferenca: "550.00", situacao: "falta" },
  });
