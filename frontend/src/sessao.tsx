import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, definirCsrf, mensagemDe } from "./api/cliente";

export interface Usuario {
  id: number;
  nome: string;
}
type Resultado = { ok: true } | { ok: false; mensagem: string };

interface Contexto {
  carregando: boolean;
  usuario: Usuario | null;
  entrar: (nome: string, senha: string) => Promise<Resultado>;
  sair: () => Promise<void>;
}

const SessaoContexto = createContext<Contexto | null>(null);

export function SessaoProvider({ children }: { children: ReactNode }) {
  const [carregando, setCarregando] = useState(true);
  const [usuario, setUsuario] = useState<Usuario | null>(null);

  useEffect(() => {
    let ativo = true;
    api
      .GET("/api/me")
      .then(({ data }) => {
        if (!ativo) return;
        if (data) {
          definirCsrf(data.csrf_token);
          setUsuario({ id: data.id, nome: data.nome });
        }
      })
      .catch(() => undefined)
      .finally(() => ativo && setCarregando(false));
    return () => {
      ativo = false;
    };
  }, []);

  const entrar = useCallback(async (nome: string, senha: string): Promise<Resultado> => {
    try {
      const { data, error, response } = await api.POST("/api/auth/login", { body: { nome, senha } });
      if (data) {
        definirCsrf(data.csrf_token);
        setUsuario({ id: data.id, nome: data.nome });
        return { ok: true };
      }
      const reserva = response.status === 401 ? "Usuário ou senha inválidos." : "Não foi possível entrar. Tente novamente.";
      return { ok: false, mensagem: mensagemDe(error, reserva) };
    } catch {
      return { ok: false, mensagem: "Não foi possível falar com o servidor. Tente novamente." };
    }
  }, []);

  const sair = useCallback(async () => {
    await api.POST("/api/auth/logout").catch(() => undefined);
    definirCsrf("");
    setUsuario(null);
  }, []);

  const valor = useMemo(() => ({ carregando, usuario, entrar, sair }), [carregando, usuario, entrar, sair]);
  return <SessaoContexto.Provider value={valor}>{children}</SessaoContexto.Provider>;
}

export function useSessao(): Contexto {
  const contexto = useContext(SessaoContexto);
  if (!contexto) throw new Error("useSessao fora do SessaoProvider");
  return contexto;
}
