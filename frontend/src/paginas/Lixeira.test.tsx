import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { renderizar, simularApi, USUARIO, type Rotas } from "../testes/api";
import { lanc } from "../testes/dados";

afterEach(() => vi.unstubAllGlobals());

const apagados = [
  lanc({ id: 1, descricao: "Mercado", valor: "100.50", apagado_em: "2026-11-01T15:30:00" }),
  lanc({ id: 2, descricao: "Cinema", valor: "40.00", dia: 9, apagado_em: "2026-11-02T10:00:00" }),
];
const base = (extra: Rotas = {}): Rotas => ({ "GET /api/me": { corpo: USUARIO }, ...extra });

describe("lixeira", () => {
  // Spec: WEB-25
  it("lista os itens apagados", async () => {
    simularApi(base({ "GET /api/lixeira": { corpo: apagados } }));
    renderizar(<App />, "/lixeira");

    const tabela = await screen.findByRole("table", { name: "Itens da lixeira" });
    const linhas = within(tabela).getAllByRole("row").slice(1);
    expect(linhas).toHaveLength(2);
    expect(linhas[0]).toHaveTextContent("Mercado");
    expect(linhas[0]).toHaveTextContent("R$ 100,50");
    expect(linhas[0]).toHaveTextContent("novembro de 2026");
  });

  // Spec: WEB-25
  it("lixeira vazia mostra um aviso e não oferece esvaziar", async () => {
    simularApi(base({ "GET /api/lixeira": { corpo: [] } }));
    renderizar(<App />, "/lixeira");

    expect(await screen.findByText("A lixeira está vazia.")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Esvaziar lixeira" })).not.toBeInTheDocument();
  });

  // Spec: WEB-25
  it("restaura sem pedir confirmação e atualiza a lista", async () => {
    let lista = [...apagados];
    const chamadas = simularApi(base({
      "GET /api/lixeira": () => ({ corpo: lista }),
      "POST /api/lixeira/1/restaurar": () => {
        lista = lista.slice(1);
        return { corpo: apagados[0] };
      },
    }));
    renderizar(<App />, "/lixeira");

    await userEvent.click(await screen.findByRole("button", { name: "Restaurar Mercado" }));

    expect(await screen.findByText('"Mercado" foi restaurado.')).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByRole("button", { name: "Restaurar Mercado" })).not.toBeInTheDocument());
    expect(chamadas.find((c) => c.caminho === "/api/lixeira/1/restaurar")?.csrf).toBe("csrf-ana");
  });

  // Spec: WEB-25, WEB-18
  it("excluir definitivamente pede confirmação, com o foco na opção segura", async () => {
    let lista = [...apagados];
    const chamadas = simularApi(base({
      "GET /api/lixeira": () => ({ corpo: lista }),
      "DELETE /api/lixeira/2": () => {
        lista = lista.filter((i) => i.id !== 2);
        return { status: 204 };
      },
    }));
    renderizar(<App />, "/lixeira");

    await userEvent.click(await screen.findByRole("button", { name: "Excluir definitivamente Cinema" }));

    const dialogo = await screen.findByRole("alertdialog");
    expect(dialogo).toHaveTextContent('Excluir "Cinema" definitivamente?');
    expect(within(dialogo).getByRole("button", { name: "Cancelar" })).toHaveFocus();
    expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(false); // ainda não enviou nada

    await userEvent.click(within(dialogo).getByRole("button", { name: "Excluir agora" }));
    expect(await screen.findByText('"Cinema" foi excluído definitivamente.')).toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "DELETE" && c.caminho === "/api/lixeira/2")).toBe(true);
  });

  // Spec: WEB-25
  it("cancelar a confirmação não exclui nada", async () => {
    const chamadas = simularApi(base({ "GET /api/lixeira": { corpo: apagados } }));
    renderizar(<App />, "/lixeira");

    await userEvent.click(await screen.findByRole("button", { name: "Excluir definitivamente Cinema" }));
    await userEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Cancelar" }));

    expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument();
    expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(false);
  });

  // Spec: WEB-25
  it("esvaziar pede confirmação e informa quantos foram excluídos", async () => {
    let lista = [...apagados];
    const chamadas = simularApi(base({
      "GET /api/lixeira": () => ({ corpo: lista }),
      "DELETE /api/lixeira": () => {
        lista = [];
        return { corpo: { removidos: 2 } };
      },
    }));
    renderizar(<App />, "/lixeira");

    await userEvent.click(await screen.findByRole("button", { name: "Esvaziar lixeira" }));
    const dialogo = await screen.findByRole("alertdialog");
    expect(dialogo).toHaveTextContent("Excluir definitivamente os 2 itens");
    expect(chamadas.some((c) => c.metodo === "DELETE")).toBe(false);

    await userEvent.click(within(dialogo).getByRole("button", { name: "Esvaziar agora" }));
    expect(await screen.findByText("2 lançamentos foram excluídos definitivamente.")).toBeInTheDocument();
    expect(await screen.findByText("A lixeira está vazia.")).toBeInTheDocument();
  });
});
