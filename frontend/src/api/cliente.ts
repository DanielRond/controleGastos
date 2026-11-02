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

export const api = createClient<paths>({
  baseUrl: typeof location === "undefined" ? "" : location.origin,
  credentials: "same-origin",
  // lido na hora da chamada, para que os testes possam trocar o fetch global
  fetch: (requisicao) => globalThis.fetch(requisicao),
});
api.use(csrf);

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
