import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./componentes/Layout";
import { RotaProtegida } from "./componentes/RotaProtegida";
import { mesAtual } from "./formato";
import { EmConstrucao } from "./paginas/EmConstrucao";
import { Login } from "./paginas/Login";

function InicioDoMes() {
  const { ano, mes } = mesAtual();
  return <Navigate to={`/mes/${ano}/${mes}`} replace />;
}

export function App() {
  return (
    <Routes>
      <Route path="/entrar" element={<Login />} />
      <Route element={<RotaProtegida />}>
        <Route element={<Layout />}>
          <Route index element={<InicioDoMes />} />
          <Route path="/mes/:ano/:mes" element={<EmConstrucao titulo="Mês" />} />
          <Route path="/ano/:ano" element={<EmConstrucao titulo="Ano" />} />
          <Route path="/lixeira" element={<EmConstrucao titulo="Lixeira" />} />
          <Route path="/arquivos" element={<EmConstrucao titulo="Arquivos" />} />
          <Route path="*" element={<InicioDoMes />} />
        </Route>
      </Route>
    </Routes>
  );
}
