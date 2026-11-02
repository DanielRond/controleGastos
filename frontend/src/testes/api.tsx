import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { vi } from "vitest";
import { SessaoProvider } from "../sessao";

export type Resposta = { status?: number; corpo?: unknown };
export type Rotas = Record<string, Resposta | ((corpo: unknown) => Resposta | Promise<Resposta>)>;
export interface Chamada {
  metodo: string;
  caminho: string;
  corpo: unknown;
  csrf: string | null;
}

/** Troca o fetch global por rotas simuladas ("GET /api/me") e devolve o registro das chamadas. */
export function simularApi(rotas: Rotas): Chamada[] {
  const chamadas: Chamada[] = [];
  vi.stubGlobal(
    "fetch",
    vi.fn(async (requisicao: Request) => {
      const url = new URL(requisicao.url);
      const texto = await requisicao.clone().text();
      const corpo = texto ? JSON.parse(texto) : undefined;
      chamadas.push({ metodo: requisicao.method, caminho: url.pathname + url.search, corpo, csrf: requisicao.headers.get("X-CSRF-Token") });
      const chave = `${requisicao.method} ${url.pathname}`;
      const definida = rotas[chave];
      if (!definida) return new Response(JSON.stringify({ detalhe: `sem rota simulada: ${chave}` }), { status: 404 });
      const { status = 200, corpo: resposta } = typeof definida === "function" ? await definida(corpo) : definida;
      return new Response(status === 204 ? null : JSON.stringify(resposta ?? {}), {
        status,
        headers: { "content-type": "application/json" },
      });
    }),
  );
  return chamadas;
}

export const USUARIO = { id: 1, nome: "ana", csrf_token: "csrf-ana" };

export function renderizar(elemento: ReactElement, rota = "/") {
  const consultas = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={consultas}>
      <MemoryRouter initialEntries={[rota]}>
        <SessaoProvider>{elemento}</SessaoProvider>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}
