import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import { App } from "./../App";
import { renderizar, simularApi, USUARIO, type Rotas } from "../testes/api";
import { lanc, mesComDados, mesVazio } from "../testes/dados";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 2));
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

const base = (extra: Rotas = {}): Rotas => ({ "GET /api/me": { corpo: USUARIO }, ...extra });

describe("tela do mês", () => {
  // Spec: WEB-22, WEB-18
  it("mostra totais, lançamentos, classes e meta em reais", async () => {
    simularApi(base({ "GET /api/meses/2026/11": { corpo: mesComDados() } }));
    renderizar(<App />, "/mes/2026/11");

    expect(await screen.findByRole("heading", { name: "Mês: novembro de 2026" })).toBeInTheDocument();
    const resumo = await screen.findByRole("region", { name: "Resumo do mês" });
    expect(within(resumo).getByText("R$ 3.200,00")).toBeInTheDocument();
    expect(within(resumo).getByText("R$ 100,50")).toBeInTheDocument();
    expect(within(resumo).getByText("R$ 2.799,50")).toBeInTheDocument();
    expect(within(resumo).getByRole("table", { name: "Investimentos por classe" })).toHaveTextContent("Fundos imobiliários (FII)");
    expect(within(resumo).getByRole("table", { name: "Investimentos por classe" })).toHaveTextContent("100,00%");
    expect(screen.getByText(/Faltam R\$ 550,00/)).toBeInTheDocument();

    const tabela = screen.getByRole("table", { name: "Lançamentos do mês" });
    const linhas = within(tabela).getAllByRole("row").slice(1);
    expect(linhas.map((l) => within(l).getAllByRole("cell")[1].textContent)).toEqual(["Mercado", "Freela", "Aporte FII"]);
    expect(linhas[2]).toHaveTextContent("Investimento (Fundos imobiliários (FII), KNSC11)");
  });

  // Spec: WEB-22
  it("mês sem lançamentos mostra um aviso, não um erro", async () => {
    simularApi(base({ "GET /api/meses/2026/11": { corpo: mesVazio() } }));
    renderizar(<App />, "/mes/2026/11");

    expect(await screen.findByText("Nenhum lançamento neste mês.")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  // Spec: WEB-22
  it("navega para o mês anterior e o seguinte, inclusive na virada de ano", async () => {
    simularApi(base({ "GET /api/meses/2026/1": { corpo: mesVazio({ ano: 2026, mes: 1 }) } }));
    renderizar(<App />, "/mes/2026/1");

    expect(await screen.findByRole("link", { name: /dezembro de 2025/ })).toHaveAttribute("href", "/mes/2025/12");
    expect(screen.getByRole("link", { name: /fevereiro de 2026/ })).toHaveAttribute("href", "/mes/2026/2");
  });

  // Spec: WEB-22
  it("escolhe outro ano e mês pelo formulário", async () => {
    simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesVazio() },
      "GET /api/meses/2025/3": { corpo: mesVazio({ ano: 2025, mes: 3 }) },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.selectOptions(await screen.findByLabelText("Mês"), "março");
    const ano = screen.getByLabelText("Ano");
    await userEvent.clear(ano);
    await userEvent.type(ano, "2025");
    await userEvent.click(screen.getByRole("button", { name: "Ir" }));

    expect(await screen.findByRole("heading", { name: "Mês: março de 2025" })).toBeInTheDocument();
  });

  // Spec: WEB-22
  it("mês inválido na URL volta para o mês atual", async () => {
    simularApi(base({ "GET /api/meses/2026/11": { corpo: mesVazio() } }));
    renderizar(<App />, "/mes/2026/13");
    expect(await screen.findByRole("heading", { name: "Mês: novembro de 2026" })).toBeInTheDocument();
  });

  // Spec: WEB-22
  it("meta ultrapassada e atingida têm mensagens próprias", async () => {
    simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesVazio({ meta: { valor: "50.00", investido: "80.00", diferenca: "-30.00", situacao: "acima" } }) },
      "GET /api/meses/2026/10": { corpo: mesVazio({ mes: 10, meta: { valor: "100.00", investido: "100.00", diferenca: "0.00", situacao: "acima" } }) },
    }));
    const { unmount } = renderizar(<App />, "/mes/2026/11");
    expect(await screen.findByText(/Meta ultrapassada em R\$ 30,00/)).toBeInTheDocument();
    unmount();
    renderizar(<App />, "/mes/2026/10");
    expect(await screen.findByText(/Meta atingida/)).toBeInTheDocument();
  });
});

describe("novo lançamento", () => {
  // Spec: WEB-22, WEB-27
  it("envia o valor em texto decimal e recarrega o mês", async () => {
    let mes = mesVazio();
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": () => ({ corpo: mes }),
      "POST /api/lancamentos": () => {
        mes = mesVazio({ lancamentos: [lanc({ id: 9, descricao: "Padaria", valor: "1234.56" })] });
        return { status: 201, corpo: lanc({ id: 9, descricao: "Padaria", valor: "1234.56" }) };
      },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.type(await screen.findByLabelText("Dia"), "7");
    await userEvent.type(screen.getByLabelText("Descrição"), "Padaria");
    await userEvent.type(screen.getByLabelText("Valor (R$)"), "1.234,56");
    await userEvent.type(screen.getByLabelText("Categoria"), "alimentacao");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    expect(await screen.findByText("R$ 1.234,56", { selector: "td" })).toBeInTheDocument();
    const envio = chamadas.find((c) => c.metodo === "POST" && c.caminho === "/api/lancamentos");
    expect(envio?.corpo).toEqual({ ano: 2026, mes: 11, tipo: "despesa", descricao: "Padaria", valor: "1234.56", dia: 7, categoria: "alimentacao" });
    expect(envio?.csrf).toBe("csrf-ana");
    expect(screen.getByLabelText("Descrição")).toHaveValue(""); // formulário limpo para o próximo
    expect(screen.getByLabelText("Categoria")).toHaveValue(""); // a categoria não vaza para o próximo lançamento
    await waitFor(() => expect(screen.getByLabelText("Dia")).toHaveFocus()); // pronto para digitar o seguinte
  });

  // Spec: WEB-22, WEB-18
  it("durante o envio os campos ficam desabilitados, para nada digitado ser apagado pela resposta", async () => {
    let liberar!: () => void;
    const espera = new Promise<void>((resolver) => (liberar = resolver));
    simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesVazio() },
      "POST /api/lancamentos": async () => {
        await espera;
        return { status: 201, corpo: lanc() };
      },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.type(await screen.findByLabelText("Dia"), "7");
    await userEvent.type(screen.getByLabelText("Descrição"), "Padaria");
    await userEvent.type(screen.getByLabelText("Valor (R$)"), "10");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    await waitFor(() => expect(screen.getByLabelText("Descrição")).toBeDisabled());
    expect(screen.getByRole("button", { name: "Adicionar" })).toBeDisabled();

    liberar();
    await waitFor(() => expect(screen.getByLabelText("Descrição")).toBeEnabled());
    expect(screen.getByLabelText("Descrição")).toHaveValue("");
  });

  // Spec: WEB-27
  it("recusa mais de duas casas antes de enviar", async () => {
    const chamadas = simularApi(base({ "GET /api/meses/2026/11": { corpo: mesVazio() } }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.type(await screen.findByLabelText("Dia"), "7");
    await userEvent.type(screen.getByLabelText("Descrição"), "x");
    await userEvent.type(screen.getByLabelText("Valor (R$)"), "10,123");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Use no máximo 2 casas decimais.");
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  // Spec: WEB-22, WEB-18
  it("mostra os erros da API junto ao campo, ligados por aria-describedby", async () => {
    simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesVazio() },
      "POST /api/lancamentos": {
        status: 422,
        corpo: { erros: [{ caminho: "dia", mensagem: "dia 31 é inválido para 11/2026 (esperado entre 1 e 30)" }, { caminho: "descricao", mensagem: "campo obrigatório 'descricao' ausente" }] },
      },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.type(await screen.findByLabelText("Dia"), "31");
    await userEvent.type(screen.getByLabelText("Valor (R$)"), "5");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    const dia = screen.getByLabelText("Dia");
    await waitFor(() => expect(dia).toHaveAttribute("aria-invalid", "true"));
    expect(document.getElementById(dia.getAttribute("aria-describedby")!)).toHaveTextContent("dia 31 é inválido");
    const descricao = screen.getByLabelText("Descrição");
    expect(document.getElementById(descricao.getAttribute("aria-describedby")!)).toHaveTextContent("campo obrigatório");
  });

  // Spec: WEB-22
  it("investimento pede classe e ativo; os outros tipos não", async () => {
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesVazio() },
      "POST /api/lancamentos": { status: 201, corpo: lanc({ tipo: "investimento" }) },
    }));
    renderizar(<App />, "/mes/2026/11");

    expect(await screen.findByLabelText("Tipo")).toHaveValue("despesa");
    expect(screen.queryByLabelText("Classe do investimento")).not.toBeInTheDocument();

    await userEvent.selectOptions(screen.getByLabelText("Tipo"), "Investimento");
    await userEvent.selectOptions(screen.getByLabelText("Classe do investimento"), "Fundos imobiliários (FII)");
    await userEvent.type(screen.getByLabelText(/Ativo/), "KNSC11");
    await userEvent.type(screen.getByLabelText("Dia"), "10");
    await userEvent.type(screen.getByLabelText("Descrição"), "Aporte");
    await userEvent.type(screen.getByLabelText("Valor (R$)"), "300");
    await userEvent.click(screen.getByRole("button", { name: "Adicionar" }));

    await waitFor(() => expect(chamadas.some((c) => c.metodo === "POST")).toBe(true));
    expect(chamadas.find((c) => c.metodo === "POST")?.corpo).toMatchObject({
      tipo: "investimento", tipo_investimento: "fii", ativo: "KNSC11", valor: "300",
    });
  });
});

describe("editar e apagar", () => {
  // Spec: WEB-22
  it("edita um lançamento com PATCH e volta ao formulário de novo", async () => {
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesComDados() },
      "PATCH /api/lancamentos/1": { corpo: lanc({ id: 1, descricao: "Feira" }) },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.click(await screen.findByRole("button", { name: "Editar Mercado" }));
    expect(screen.getByRole("heading", { name: "Editar lançamento" })).toBeInTheDocument();
    expect(screen.getByLabelText("Valor (R$)")).toHaveValue("100,50");
    expect(screen.getByLabelText("Tipo")).toBeDisabled();

    const descricao = screen.getByLabelText("Descrição");
    await userEvent.clear(descricao);
    await userEvent.type(descricao, "Feira");
    await userEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));

    await waitFor(() => expect(screen.getByRole("heading", { name: "Novo lançamento" })).toBeInTheDocument());
    const envio = chamadas.find((c) => c.metodo === "PATCH");
    expect(envio?.caminho).toBe("/api/lancamentos/1");
    expect(envio?.corpo).toMatchObject({ descricao: "Feira", valor: "100.50", dia: 3 });
  });

  // Spec: WEB-22
  it("cancelar a edição não envia nada", async () => {
    const chamadas = simularApi(base({ "GET /api/meses/2026/11": { corpo: mesComDados() } }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.click(await screen.findByRole("button", { name: "Editar Mercado" }));
    await userEvent.click(screen.getByRole("button", { name: "Cancelar" }));

    expect(screen.getByRole("heading", { name: "Novo lançamento" })).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "PATCH")).toBe(false);
  });

  // Spec: WEB-22
  it("apagar move para a lixeira e avisa com link", async () => {
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesComDados() },
      "DELETE /api/lancamentos/1": { status: 204 },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.click(await screen.findByRole("button", { name: "Apagar Mercado" }));

    const aviso = await screen.findByText(/"Mercado" foi movido para a lixeira/);
    expect(aviso).toBeInTheDocument();
    expect(within(aviso.closest("p")!).getByRole("link", { name: "Abrir a lixeira" })).toHaveAttribute("href", "/lixeira");
    expect(chamadas.some((c) => c.metodo === "DELETE" && c.caminho === "/api/lancamentos/1")).toBe(true);
  });
});

describe("salário e meta", () => {
  // Spec: WEB-23
  it("mostra os valores atuais, salva e envia texto decimal; o aviso de salvo permanece depois de recarregar", async () => {
    let atual = mesComDados();
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": () => ({ corpo: atual }),
      "PUT /api/meses/2026/11": (corpo) => {
        atual = { ...atual, salario: (corpo as { salario: string }).salario };
        return { corpo: atual };
      },
    }));
    renderizar(<App />, "/mes/2026/11");

    const salario = await screen.findByLabelText("Salário (R$)");
    expect(salario).toHaveValue("3000,00");
    expect(screen.getByLabelText("Meta de investimento (R$)")).toHaveValue("850,00");

    await userEvent.clear(salario);
    await userEvent.type(salario, "3.500,25");
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));

    // o servidor agora devolve o salário novo; mesmo assim a confirmação continua na tela
    expect(await screen.findByText("Salário e meta salvos.")).toBeInTheDocument();
    await waitFor(() => expect(screen.getByLabelText("Salário (R$)")).toHaveValue("3500,25"));
    expect(screen.getByText("Salário e meta salvos.")).toBeInTheDocument();
    expect(chamadas.find((c) => c.metodo === "PUT")?.corpo).toEqual({ salario: "3500.25", meta_investimento: "850.00" });

    await userEvent.type(screen.getByLabelText("Salário (R$)"), "1"); // voltar a editar esconde o aviso
    expect(screen.queryByText("Salário e meta salvos.")).not.toBeInTheDocument();
  });

  // Spec: WEB-23
  it("campo em branco limpa o valor (null)", async () => {
    const chamadas = simularApi(base({
      "GET /api/meses/2026/11": { corpo: mesComDados() },
      "PUT /api/meses/2026/11": { corpo: mesVazio() },
    }));
    renderizar(<App />, "/mes/2026/11");

    await userEvent.clear(await screen.findByLabelText("Meta de investimento (R$)"));
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));

    await waitFor(() => expect(chamadas.some((c) => c.metodo === "PUT")).toBe(true));
    expect(chamadas.find((c) => c.metodo === "PUT")?.corpo).toEqual({ salario: "3000.00", meta_investimento: null });
  });

  // Spec: WEB-23, WEB-27
  it("valor inválido é recusado no campo, sem enviar", async () => {
    const chamadas = simularApi(base({ "GET /api/meses/2026/11": { corpo: mesComDados() } }));
    renderizar(<App />, "/mes/2026/11");

    const salario = await screen.findByLabelText("Salário (R$)");
    await userEvent.clear(salario);
    await userEvent.type(salario, "10,999");
    await userEvent.click(screen.getByRole("button", { name: "Salvar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Use no máximo 2 casas decimais.");
    expect(chamadas.some((c) => c.metodo === "PUT")).toBe(false);
  });
});
