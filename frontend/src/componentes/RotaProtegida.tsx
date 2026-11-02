import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useSessao } from "../sessao";

/** Sem sessão, leva ao login e guarda de onde a pessoa veio (WEB-21). */
export function RotaProtegida() {
  const { carregando, usuario } = useSessao();
  const local = useLocation();
  if (carregando) return <p role="status">Carregando…</p>;
  if (!usuario) return <Navigate to="/entrar" replace state={{ de: local.pathname + local.search }} />;
  return <Outlet />;
}
