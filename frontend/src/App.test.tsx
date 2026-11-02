import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import { App } from "./App";
import { renderizar, simularApi, USUARIO } from "./testes/api";

beforeEach(() => {
  vi.useFakeTimers({ toFake: ["Date"] });
  vi.setSystemTime(new Date(2026, 10, 2)); // novembro de 2026
});
afterEach(() => {
  vi.useRealTimers();
  vi.unstubAllGlobals();
});

describe("login", () => {
  // Spec: WEB-20, WEB-18
  it("tem campos rotulados e entra no mês atual", async () => {
    const chamadas = simularApi({
      "GET /api/me": { status: 401, corpo: { detalhe: "É preciso entrar." } },
      "POST /api/auth/login": { corpo: USUARIO },
    });
    renderizar(<App />, "/entrar");

    const usuario = await screen.findByLabelText("Usuário");
    await userEvent.type(usuario, "ana");
    await userEvent.type(screen.getByLabelText("Senha"), "senha-segura-123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("heading", { name: "Mês" })).toBeInTheDocument();
    const login = chamadas.find((c) => c.caminho === "/api/auth/login");
    expect(login?.corpo).toEqual({ nome: "ana", senha: "senha-segura-123" });
  });

  // Spec: WEB-20, WEB-18
  it("mostra erro genérico e anunciado quando as credenciais falham", async () => {
    simularApi({
      "GET /api/me": { status: 401, corpo: { detalhe: "É preciso entrar." } },
      "POST /api/auth/login": { status: 401, corpo: { detalhe: "Usuário ou senha inválidos." } },
    });
    renderizar(<App />, "/entrar");

    await userEvent.type(await screen.findByLabelText("Usuário"), "ana");
    await userEvent.type(screen.getByLabelText("Senha"), "errada-errada");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Usuário ou senha inválidos.");
    expect(screen.queryByRole("heading", { name: "Mês" })).not.toBeInTheDocument();
  });

  // Spec: WEB-20
  it("explica o bloqueio por tentativas (429)", async () => {
    simularApi({
      "GET /api/me": { status: 401, corpo: { detalhe: "x" } },
      "POST /api/auth/login": {
        status: 429,
        corpo: { detalhe: "Muitas tentativas de login. Aguarde alguns minutos e tente de novo." },
      },
    });
    renderizar(<App />, "/entrar");

    await userEvent.type(await screen.findByLabelText("Usuário"), "ana");
    await userEvent.type(screen.getByLabelText("Senha"), "qualquer-coisa");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Muitas tentativas de login");
  });

  // Spec: WEB-20
  it("é navegável por teclado: Tab percorre usuário, senha e botão", async () => {
    simularApi({ "GET /api/me": { status: 401, corpo: { detalhe: "x" } } });
    renderizar(<App />, "/entrar");
    const usuario = await screen.findByLabelText("Usuário");
    expect(usuario).toHaveFocus();
    await userEvent.tab();
    expect(screen.getByLabelText("Senha")).toHaveFocus();
    await userEvent.tab();
    expect(screen.getByRole("button", { name: "Entrar" })).toHaveFocus();
  });
});

describe("rotas protegidas", () => {
  // Spec: WEB-21
  it("sem sessão, qualquer tela leva ao login", async () => {
    simularApi({ "GET /api/me": { status: 401, corpo: { detalhe: "x" } } });
    renderizar(<App />, "/lixeira");
    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
  });

  // Spec: WEB-21
  it("depois de entrar, volta para a tela que a pessoa queria", async () => {
    simularApi({
      "GET /api/me": { status: 401, corpo: { detalhe: "x" } },
      "POST /api/auth/login": { corpo: USUARIO },
    });
    renderizar(<App />, "/lixeira");

    await userEvent.type(await screen.findByLabelText("Usuário"), "ana");
    await userEvent.type(screen.getByLabelText("Senha"), "senha-segura-123");
    await userEvent.click(screen.getByRole("button", { name: "Entrar" }));

    expect(await screen.findByRole("heading", { name: "Lixeira" })).toBeInTheDocument();
  });

  // Spec: WEB-21
  it("com sessão, o cabeçalho tem os links, o nome e o botão Sair", async () => {
    simularApi({ "GET /api/me": { corpo: USUARIO } });
    renderizar(<App />, "/");

    const navegacao = await screen.findByRole("navigation", { name: "Principal" });
    expect(within(navegacao).getByRole("link", { name: "Mês" })).toHaveAttribute("href", "/mes/2026/11");
    expect(within(navegacao).getByRole("link", { name: "Ano" })).toHaveAttribute("href", "/ano/2026");
    expect(within(navegacao).getByRole("link", { name: "Lixeira" })).toBeInTheDocument();
    expect(within(navegacao).getByRole("link", { name: "Arquivos" })).toBeInTheDocument();
    expect(screen.getByText("ana")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Ir para o conteúdo" })).toBeInTheDocument();
  });

  // Spec: WEB-21
  it("Sair encerra a sessão e volta ao login", async () => {
    const chamadas = simularApi({
      "GET /api/me": { corpo: USUARIO },
      "POST /api/auth/logout": { status: 204 },
    });
    renderizar(<App />, "/");

    await userEvent.click(await screen.findByRole("button", { name: "Sair" }));

    expect(await screen.findByRole("heading", { name: "Entrar" })).toBeInTheDocument();
    await waitFor(() => expect(chamadas.some((c) => c.caminho === "/api/auth/logout")).toBe(true));
  });

  // Spec: WEB-21
  it("as escritas levam o token CSRF da sessão", async () => {
    const chamadas = simularApi({
      "GET /api/me": { corpo: USUARIO },
      "POST /api/auth/logout": { status: 204 },
    });
    renderizar(<App />, "/");
    await userEvent.click(await screen.findByRole("button", { name: "Sair" }));

    await waitFor(() => expect(chamadas.find((c) => c.caminho === "/api/auth/logout")?.csrf).toBe("csrf-ana"));
    expect(chamadas.find((c) => c.metodo === "GET")?.csrf).toBeNull();
  });
});
