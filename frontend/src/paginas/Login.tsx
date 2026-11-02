import { useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { mesAtual } from "../formato";
import { useSessao } from "../sessao";

export function Login() {
  const { usuario, entrar } = useSessao();
  const navegar = useNavigate();
  const local = useLocation();
  const [nome, setNome] = useState("");
  const [senha, setSenha] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  const { ano, mes } = mesAtual();
  const destino = (local.state as { de?: string } | null)?.de ?? `/mes/${ano}/${mes}`;

  if (usuario) return <Navigate to={destino} replace />;

  async function enviar(evento: FormEvent) {
    evento.preventDefault();
    setErro(null);
    setEnviando(true);
    const resultado = await entrar(nome, senha);
    setEnviando(false);
    if (resultado.ok) navegar(destino, { replace: true });
    else setErro(resultado.mensagem);
  }

  return (
    <main className="login">
      <form onSubmit={enviar} aria-labelledby="titulo-login">
        <h1 id="titulo-login">Entrar</h1>
        <div className="campo">
          <label htmlFor="nome">Usuário</label>
          <input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} autoComplete="username" required autoFocus />
        </div>
        <div className="campo">
          <label htmlFor="senha">Senha</label>
          <input id="senha" type="password" value={senha} onChange={(e) => setSenha(e.target.value)} autoComplete="current-password" required />
        </div>
        {erro && (
          <p role="alert" className="erro">
            {erro}
          </p>
        )}
        <button type="submit" disabled={enviando}>
          {enviando ? "Entrando…" : "Entrar"}
        </button>
      </form>
    </main>
  );
}
