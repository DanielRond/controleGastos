import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { api, mensagemDe } from "../api/cliente";
import type { Lancamento } from "../api/tipos";
import { Confirmacao } from "../componentes/Confirmacao";
import { formatarReais, nomeDoMes } from "../formato";

type Pendente = { tipo: "item"; item: Lancamento } | { tipo: "esvaziar" } | null;

function apagadoEm(iso: string | null | undefined): string {
  if (!iso) return "";
  const data = new Date(iso.endsWith("Z") || /[+-]\d\d:\d\d$/.test(iso) ? iso : `${iso}Z`);
  return data.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

export function Lixeira() {
  const clienteDeConsultas = useQueryClient();
  const [pendente, setPendente] = useState<Pendente>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);

  const consulta = useQuery({
    queryKey: ["lixeira"],
    queryFn: async () => {
      const { data, error } = await api.GET("/api/lixeira");
      if (!data) throw new Error(mensagemDe(error, "Não foi possível carregar a lixeira."));
      return data;
    },
  });

  function depoisDeAgir(texto: string) {
    setPendente(null);
    setMensagem(texto);
    void clienteDeConsultas.invalidateQueries({ queryKey: ["lixeira"] });
    void clienteDeConsultas.invalidateQueries({ queryKey: ["mes"] });
    void clienteDeConsultas.invalidateQueries({ queryKey: ["ano"] });
  }

  const restaurar = useMutation({
    mutationFn: async (item: Lancamento) => {
      const { error } = await api.POST("/api/lixeira/{id}/restaurar", { params: { path: { id: item.id } } });
      if (error) throw new Error(mensagemDe(error, "Não foi possível restaurar."));
      return item;
    },
    onSuccess: (item) => depoisDeAgir(`"${item.descricao}" foi restaurado.`),
    onError: (e: Error) => setMensagem(e.message),
  });

  const excluir = useMutation({
    mutationFn: async (item: Lancamento) => {
      const { error } = await api.DELETE("/api/lixeira/{id}", { params: { path: { id: item.id } } });
      if (error) throw new Error(mensagemDe(error, "Não foi possível excluir."));
      return item;
    },
    onSuccess: (item) => depoisDeAgir(`"${item.descricao}" foi excluído definitivamente.`),
    onError: (e: Error) => setMensagem(e.message),
  });

  const esvaziar = useMutation({
    mutationFn: async () => {
      const { data, error } = await api.DELETE("/api/lixeira");
      if (!data) throw new Error(mensagemDe(error, "Não foi possível esvaziar a lixeira."));
      return data.removidos;
    },
    onSuccess: (n) => depoisDeAgir(n === 1 ? "1 lançamento foi excluído definitivamente." : `${n} lançamentos foram excluídos definitivamente.`),
    onError: (e: Error) => setMensagem(e.message),
  });

  const itens = consulta.data ?? [];

  return (
    <section>
      <h1>Lixeira</h1>
      <p className="aviso">Os itens daqui não entram nos totais, nos gráficos nem nos arquivos. Ficam até você excluí-los.</p>

      {consulta.isPending && <p role="status">Carregando…</p>}
      {consulta.isError && (
        <p role="alert" className="erro">
          {consulta.error.message}
        </p>
      )}
      {mensagem && <p role="status" className="aviso-acao">{mensagem}</p>}

      {consulta.data && itens.length === 0 && <p className="aviso">A lixeira está vazia.</p>}

      {itens.length > 0 && (
        <>
          <div className="botoes">
            <button type="button" className="perigo" onClick={() => setPendente({ tipo: "esvaziar" })}>
              Esvaziar lixeira
            </button>
          </div>
          {pendente?.tipo === "esvaziar" && (
            <Confirmacao
              mensagem={`Excluir definitivamente os ${itens.length} itens da lixeira? Isso não pode ser desfeito.`}
              rotuloConfirmar="Esvaziar agora"
              aoConfirmar={() => esvaziar.mutate()}
              aoCancelar={() => setPendente(null)}
            />
          )}
          <table aria-label="Itens da lixeira">
            <thead>
              <tr>
                <th>Mês</th>
                <th>Dia</th>
                <th>Descrição</th>
                <th>Tipo</th>
                <th className="valor">Valor</th>
                <th>Apagado em</th>
                <th>Ações</th>
              </tr>
            </thead>
            <tbody>
              {itens.map((item) => (
                <tr key={item.id}>
                  <td>
                    {nomeDoMes(item.mes)} de {item.ano}
                  </td>
                  <td>{item.dia}</td>
                  <td>{item.descricao}</td>
                  <td>{item.tipo}</td>
                  <td className="valor">{formatarReais(item.valor)}</td>
                  <td>{apagadoEm(item.apagado_em)}</td>
                  <td>
                    {pendente?.tipo === "item" && pendente.item.id === item.id ? (
                      <Confirmacao
                        mensagem={`Excluir "${item.descricao}" definitivamente? Isso não pode ser desfeito.`}
                        rotuloConfirmar="Excluir agora"
                        aoConfirmar={() => excluir.mutate(item)}
                        aoCancelar={() => setPendente(null)}
                      />
                    ) : (
                      <div className="acoes">
                        <button type="button" className="secundario" onClick={() => restaurar.mutate(item)} aria-label={`Restaurar ${item.descricao}`}>
                          Restaurar
                        </button>
                        <button type="button" className="perigo" onClick={() => setPendente({ tipo: "item", item })} aria-label={`Excluir definitivamente ${item.descricao}`}>
                          Excluir definitivamente
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </section>
  );
}
