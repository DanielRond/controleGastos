import { screen, within } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";
import { App } from "../App";
import { renderizar, simularApi, USUARIO, type Rotas } from "../testes/api";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 2));
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const resumo2026 = {
  ano: 2026,
  meses: [
    { mes: 1, receitas: "3000.00", despesas: "1200.50", investimentos: "500.00", saldo_livre: "1299.50" },
    { mes: 2, receitas: "3000.00", despesas: "2500.00", investimentos: "100.00", saldo_livre: "400.00" },
  ],
  patrimonio: [{ rotulo: "2026-01", valor: "1500.00" }, { rotulo: "2026-02", valor: "1600.00" }],
  ranking: [{ categoria: "moradia", total: "2000.00" }, { categoria: "Sem categoria", total: "1700.50" }],
  variacao: [{ rotulo: "2026-02", valor: "-899.50" }],
};
const base = (extra: Rotas = {}): Rotas => ({ "GET /api/me": { corpo: USUARIO }, ...extra });

describe("tela do ano", () => {
  // Spec: WEB-24, WEB-18
  it("mostra o resumo por mês, com link para cada mês", async () => {
    simularApi(base({ "GET /api/anos/2026/resumo": { corpo: resumo2026 } }));
    renderizar(<App />, "/ano/2026");

    const tabela = await screen.findByRole("table", { name: "Resumo por mês" });
    const linhas = within(tabela).getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(2);
    expect(linhas[0]).toHaveTextContent("janeiro");
    expect(linhas[0]).toHaveTextContent("R$ 3.000,00");
    expect(linhas[0]).toHaveTextContent("R$ 1.200,50");
    expect(linhas[1]).toHaveTextContent("R$ 400,00");
    expect(within(linhas[0]).getByRole("link", { name: "janeiro" })).toHaveAttribute("href", "/mes/2026/1");
  });

  // Spec: WEB-24, WEB-18
  it("os três gráficos têm nome e a mesma informação em tabela de texto", async () => {
    simularApi(base({ "GET /api/anos/2026/resumo": { corpo: resumo2026 } }));
    renderizar(<App />, "/ano/2026");

    expect(await screen.findByRole("img", { name: "Evolução do patrimônio (aportes acumulados)" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Ranking de categorias de despesa" })).toBeInTheDocument();
    expect(screen.getByRole("img", { name: "Variação do saldo livre entre meses" })).toBeInTheDocument();

    const patrimonio = screen.getByRole("table", { name: "Dados da evolução do patrimônio", hidden: true });
    expect(patrimonio).toHaveTextContent("R$ 1.600,00");
    expect(screen.getByRole("table", { name: "Dados do ranking de categorias", hidden: true })).toHaveTextContent("Sem categoria");
    expect(screen.getByRole("table", { name: "Dados da variação do saldo", hidden: true })).toHaveTextContent("-R$ 899,50");
  });

  // Spec: WEB-24
  it("ano sem dados mostra um aviso, não um erro", async () => {
    simularApi(base({ "GET /api/anos/1999/resumo": { corpo: { ano: 1999, meses: [], patrimonio: [], ranking: [], variacao: [] } } }));
    renderizar(<App />, "/ano/1999");

    expect(await screen.findByText("Sem lançamentos em 1999.")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
  });

  // Spec: WEB-24
  it("navega para o ano anterior e o seguinte", async () => {
    simularApi(base({ "GET /api/anos/2026/resumo": { corpo: resumo2026 } }));
    renderizar(<App />, "/ano/2026");

    expect(await screen.findByRole("link", { name: /2025/ })).toHaveAttribute("href", "/ano/2025");
    expect(screen.getByRole("link", { name: /2027/ })).toHaveAttribute("href", "/ano/2027");
  });

  // Spec: WEB-24
  it("não recalcula: os números mostrados são os que a API enviou", async () => {
    const adulterado = { ...resumo2026, meses: [{ mes: 1, receitas: "1.00", despesas: "1.00", investimentos: "1.00", saldo_livre: "777.77" }] };
    simularApi(base({ "GET /api/anos/2026/resumo": { corpo: adulterado } }));
    renderizar(<App />, "/ano/2026");

    expect(await screen.findByText("R$ 777,77")).toBeInTheDocument(); // saldo diferente da conta 1-1-1, mas é o da API
  });
});
