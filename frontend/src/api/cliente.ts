import createClient, { type Middleware } from "openapi-fetch";
import type { components, paths } from "./schema";

export type ErroCampo = components["schemas"]["ErroCampo"];

let tokenCsrf = "";
export function definirCsrf(token: string): void {
  tokenCsrf = token;
}

// Toda escrita leva o token CSRF da sessão (WEB-03 da API).
const csrf: Middleware = {
  onRequest({ request }) {
    if (tokenCsrf && !["GET", "HEAD", "OPTIONS"].includes(request.method)) {
      request.headers.set("X-CSRF-Token", tokenCsrf);
    }
    return request;
  },
};

// Sessão que expira no meio do uso: avisa a aplicação, que volta ao login (WEB-21).
export const EVENTO_SESSAO_EXPIRADA = "sessao-expirada";
const sessaoExpirada: Middleware = {
  onResponse({ request, response }) {
    const caminho = new URL(request.url).pathname;
    if (response.status === 401 && !["/api/auth/login", "/api/me", "/api/auth/logout"].includes(caminho)) {
      globalThis.dispatchEvent(new Event(EVENTO_SESSAO_EXPIRADA));
    }
    return response;
  },
};

export const api = createClient<paths>({
  baseUrl: typeof location === "undefined" ? "" : location.origin,
  credentials: "same-origin",
  // lido na hora da chamada, para que os testes possam trocar o fetch global
  fetch: (requisicao) => globalThis.fetch(requisicao),
});
api.use(csrf);
api.use(sessaoExpirada);

/** Erros de validação da API (422), com caminho e mensagem em português. */
export function errosDeValidacao(erro: unknown): ErroCampo[] | null {
  const lista = (erro as { erros?: unknown } | undefined)?.erros;
  return Array.isArray(lista) ? (lista as ErroCampo[]) : null;
}

/** Mensagem {"detalhe": ...} da API, ou o texto de reserva. */
export function mensagemDe(erro: unknown, reserva: string): string {
  const detalhe = (erro as { detalhe?: unknown } | undefined)?.detalhe;
  return typeof detalhe === "string" ? detalhe : reserva;
}
