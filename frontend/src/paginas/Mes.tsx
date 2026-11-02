import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Link, Navigate, useParams } from "react-router-dom";
import { api, mensagemDe } from "../api/cliente";
import type { Lancamento } from "../api/tipos";
import { FormularioLancamento } from "../componentes/FormularioLancamento";
import { NavegacaoDeMes } from "../componentes/NavegacaoDeMes";
import { ResumoDoMes } from "../componentes/ResumoDoMes";
import { SalarioEMeta } from "../componentes/SalarioEMeta";
import { TabelaLancamentos } from "../componentes/TabelaLancamentos";
import { mesAtual, nomeDoMes } from "../formato";

export function Mes() {
  const parametros = useParams();
  const ano = Number(parametros.ano);
  const mes = Number(parametros.mes);
  const valido = Number.isInteger(ano) && ano >= 1 && ano <= 9999 && Number.isInteger(mes) && mes >= 1 && mes <= 12;
  const clienteDeConsultas = useQueryClient();
  const [editando, setEditando] = useState<Lancamento | null>(null);
  const [aviso, setAviso] = useState<string | null>(null);
  const [metaSalva, setMetaSalva] = useState(false);

  const consulta = useQuery({
    queryKey: ["mes", ano, mes],
    enabled: valido,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/meses/{ano}/{mes}", { params: { path: { ano, mes } } });
      if (!data) throw new Error(mensagemDe(error, "Não foi possível carregar o mês."));
      return data;
    },
  });

  const apagar = useMutation({
    mutationFn: async (item: Lancamento) => {
      const { error } = await api.DELETE("/api/lancamentos/{id}", { params: { path: { id: item.id } } });
      if (error) throw new Error(mensagemDe(error, "Não foi possível apagar o lançamento."));
      return item;
    },
    onSuccess: (item) => {
      setAviso(`"${item.descricao}" foi movido para a lixeira.`);
      atualizar();
    },
    onError: (erro: Error) => setAviso(erro.message),
  });

  function atualizar() {
    void clienteDeConsultas.invalidateQueries({ queryKey: ["mes"] });
    void clienteDeConsultas.invalidateQueries({ queryKey: ["ano"] });
    void clienteDeConsultas.invalidateQueries({ queryKey: ["lixeira"] });
  }

  if (!valido) {
    const atual = mesAtual();
    return <Navigate to={`/mes/${atual.ano}/${atual.mes}`} replace />;
  }

  return (
    <section>
      <h1>
        Mês: {nomeDoMes(mes)} de {ano}
      </h1>
      <NavegacaoDeMes ano={ano} mes={mes} />

      {consulta.isPending && <p role="status">Carregando…</p>}
      {consulta.isError && (
        <p role="alert" className="erro">
          {consulta.error.message}
        </p>
      )}
      {aviso && (
        <p role="status" className="aviso-acao">
          {aviso} <Link to="/lixeira">Abrir a lixeira</Link>
        </p>
      )}

      {consulta.data && (
        <>
          <ResumoDoMes mes={consulta.data} />
          <h2>Lançamentos</h2>
          <TabelaLancamentos
            lancamentos={consulta.data.lancamentos}
            aoEditar={(item) => {
              setAviso(null);
              setEditando(item);
            }}
            aoApagar={(item) => apagar.mutate(item)}
          />
          <div className="colunas">
            <FormularioLancamento
              key={editando?.id ?? "novo"}
              ano={ano}
              mes={mes}
              inicial={editando ?? undefined}
              aoSalvar={() => {
                setEditando(null);
                setAviso(null);
                setMetaSalva(false);
                atualizar();
              }}
              aoCancelar={editando ? () => setEditando(null) : undefined}
            />
            <SalarioEMeta
              key={`${consulta.data.salario}-${consulta.data.meta_investimento}`}
              ano={ano}
              mes={mes}
              salario={consulta.data.salario}
              meta={consulta.data.meta_investimento}
              salvo={metaSalva}
              aoAlterar={() => setMetaSalva(false)}
              aoSalvar={() => {
                setMetaSalva(true);
                atualizar();
              }}
            />
          </div>
        </>
      )}
    </section>
  );
}
