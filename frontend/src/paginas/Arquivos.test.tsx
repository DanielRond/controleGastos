import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, vi } from "vitest";
import { App } from "../App";
import { renderizar, simularApi, USUARIO, type Rotas } from "../testes/api";

afterEach(() => vi.unstubAllGlobals());

const base = (extra: Rotas = {}): Rotas => ({ "GET /api/me": { corpo: USUARIO }, ...extra });
const documento = { anos: [{ ano: 2025, meses: [{ mes: 1, despesas: [{ descricao: "x", valor: 1.5, dia: 2 }] }] }] };
const arquivoJson = (conteudo: unknown = documento) => new File([JSON.stringify(conteudo)], "dados.json", { type: "application/json" });

describe("baixar", () => {
  // Spec: WEB-26
  it("links de planilha, CSV e JSON para todos os anos", async () => {
    simularApi(base());
    renderizar(<App />, "/arquivos");

    expect(await screen.findByRole("link", { name: "Baixar planilha (.xlsx)" })).toHaveAttribute("href", "/api/exportar/xlsx");
    expect(screen.getByRole("link", { name: "Baixar CSV (.zip)" })).toHaveAttribute("href", "/api/exportar/csv");
    expect(screen.getByRole("link", { name: "Exportar JSON" })).toHaveAttribute("href", "/api/exportar/json");
  });

  // Spec: WEB-26
  it("escolher um ano acrescenta ?ano= aos três links", async () => {
    simularApi(base());
    renderizar(<App />, "/arquivos");

    await userEvent.click(await screen.findByLabelText("Um ano"));
    const ano = screen.getByLabelText("Ano");
    await userEvent.clear(ano);
    await userEvent.type(ano, "2025");

    expect(screen.getByRole("link", { name: "Baixar planilha (.xlsx)" })).toHaveAttribute("href", "/api/exportar/xlsx?ano=2025");
    expect(screen.getByRole("link", { name: "Baixar CSV (.zip)" })).toHaveAttribute("href", "/api/exportar/csv?ano=2025");
    expect(screen.getByRole("link", { name: "Exportar JSON" })).toHaveAttribute("href", "/api/exportar/json?ano=2025");
  });
});

describe("importar", () => {
  // Spec: WEB-26
  it("importa e diz quantos lançamentos criou", async () => {
    const chamadas = simularApi(base({
      "POST /api/importar/json": { corpo: { lancamentos_criados: 1, meses: [{ ano: 2025, mes: 1 }], substituidos: 0 } },
    }));
    renderizar(<App />, "/arquivos");

    await userEvent.upload(await screen.findByLabelText("Arquivo JSON"), arquivoJson());

    expect(await screen.findByText(/1 lançamentos criados \(2025-01\)/)).toBeInTheDocument();
    const envio = chamadas.find((c) => c.metodo === "POST");
    expect(envio?.caminho).toBe("/api/importar/json?substituir=false");
    expect(envio?.corpo).toEqual(documento);
    expect(envio?.csrf).toBe("csrf-ana");
  });

  // Spec: WEB-26
  it("mostra cada erro de validação com o caminho e diz que nada foi importado", async () => {
    simularApi(base({
      "POST /api/importar/json": {
        status: 422,
        corpo: { erros: [{ caminho: "anos[0].meses[0].mes", mensagem: "mes deve ser um inteiro entre 1 e 12" }, { caminho: "anos[0].meses[0].despesas[0].dia", mensagem: "campo obrigatório 'dia' ausente" }] },
      },
    }));
    renderizar(<App />, "/arquivos");

    await userEvent.upload(await screen.findByLabelText("Arquivo JSON"), arquivoJson());

    const alerta = await screen.findByRole("alert");
    expect(alerta).toHaveTextContent("2 erro(s) e nada foi importado");
    expect(within(alerta).getByText("anos[0].meses[0].mes")).toBeInTheDocument();
    expect(alerta).toHaveTextContent("campo obrigatório 'dia' ausente");
  });

  // Spec: WEB-26
  it("arquivo que não é JSON é recusado sem falar com a API", async () => {
    const chamadas = simularApi(base());
    renderizar(<App />, "/arquivos");

    await userEvent.upload(await screen.findByLabelText("Arquivo JSON"), new File(["isto não é json"], "x.json", { type: "application/json" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("O arquivo não é um JSON válido.");
    expect(chamadas.some((c) => c.metodo === "POST")).toBe(false);
  });

  // Spec: WEB-26
  it("mês existente: avisa, oferece substituir e só substitui depois de confirmar", async () => {
    const chamadas = simularApi(base({
      "POST /api/importar/json": (corpo) => {
        void corpo;
        return chamadas.filter((c) => c.metodo === "POST").length === 1
          ? { status: 409, corpo: { mensagem: "já existem dados nos meses: 2025-01; use substituir para trocá-los", meses: [{ ano: 2025, mes: 1 }] } }
          : { corpo: { lancamentos_criados: 1, meses: [{ ano: 2025, mes: 1 }], substituidos: 4 } };
      },
    }));
    renderizar(<App />, "/arquivos");

    await userEvent.upload(await screen.findByLabelText("Arquivo JSON"), arquivoJson());
    const aviso = await screen.findByRole("alert");
    expect(aviso).toHaveTextContent("já existem dados nos meses: 2025-01");

    await userEvent.click(within(aviso).getByRole("button", { name: "Substituir os meses do arquivo" }));
    const dialogo = await screen.findByRole("alertdialog");
    expect(chamadas.filter((c) => c.metodo === "POST")).toHaveLength(1); // ainda não substituiu
    expect(within(dialogo).getByRole("button", { name: "Cancelar" })).toHaveFocus();

    await userEvent.click(within(dialogo).getByRole("button", { name: "Substituir agora" }));
    expect(await screen.findByText(/4 lançamentos antigos foram para a lixeira/)).toBeInTheDocument();
    const posts = chamadas.filter((c) => c.metodo === "POST");
    expect(posts[1].caminho).toBe("/api/importar/json?substituir=true");
    expect(posts[1].corpo).toEqual(documento);
  });

  // Spec: WEB-26
  it("cancelar a substituição não envia de novo", async () => {
    const chamadas = simularApi(base({
      "POST /api/importar/json": { status: 409, corpo: { mensagem: "já existem dados nos meses: 2025-01", meses: [{ ano: 2025, mes: 1 }] } },
    }));
    renderizar(<App />, "/arquivos");

    await userEvent.upload(await screen.findByLabelText("Arquivo JSON"), arquivoJson());
    await userEvent.click(await screen.findByRole("button", { name: "Substituir os meses do arquivo" }));
    await userEvent.click(within(await screen.findByRole("alertdialog")).getByRole("button", { name: "Cancelar" }));

    await waitFor(() => expect(screen.queryByRole("alertdialog")).not.toBeInTheDocument());
    expect(chamadas.filter((c) => c.metodo === "POST")).toHaveLength(1);
  });
});
