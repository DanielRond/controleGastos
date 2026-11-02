import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { mesAtual } from "../formato";
import { useSessao } from "../sessao";

export function Layout() {
  const { usuario, sair } = useSessao();
  const navegar = useNavigate();
  const { ano, mes } = mesAtual();

  async function aoSair() {
    await sair();
    navegar("/entrar", { replace: true });
  }

  return (
    <>
      <a className="pular" href="#conteudo">
        Ir para o conteúdo
      </a>
      <header className="cabecalho">
        <strong className="marca">controleGastos</strong>
        <nav aria-label="Principal">
          <NavLink to={`/mes/${ano}/${mes}`}>Mês</NavLink>
          <NavLink to={`/ano/${ano}`}>Ano</NavLink>
          <NavLink to="/lixeira">Lixeira</NavLink>
          <NavLink to="/arquivos">Arquivos</NavLink>
        </nav>
        <span className="usuario">{usuario?.nome}</span>
        <button type="button" onClick={aoSair}>
          Sair
        </button>
      </header>
      <main id="conteudo" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
