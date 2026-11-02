import { Navigate, Route, Routes } from "react-router-dom";
import { Layout } from "./componentes/Layout";
import { RotaProtegida } from "./componentes/RotaProtegida";
import { mesAtual } from "./formato";
import { Ano } from "./paginas/Ano";
import { Arquivos } from "./paginas/Arquivos";
import { Lixeira } from "./paginas/Lixeira";
import { Login } from "./paginas/Login";
import { Mes } from "./paginas/Mes";

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
          <Route path="/mes/:ano/:mes" element={<Mes />} />
          <Route path="/ano/:ano" element={<Ano />} />
          <Route path="/lixeira" element={<Lixeira />} />
          <Route path="/arquivos" element={<Arquivos />} />
          <Route path="*" element={<InicioDoMes />} />
        </Route>
      </Route>
    </Routes>
  );
}
