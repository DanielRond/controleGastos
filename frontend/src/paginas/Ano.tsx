import { useQuery } from "@tanstack/react-query";
import { Link, Navigate, useParams } from "react-router-dom";
import { api, mensagemDe } from "../api/cliente";
import { Grafico } from "../componentes/Grafico";
import { formatarReais, mesAtual, nomeDoMes } from "../formato";

// Os gráficos precisam de números só para desenhar; todo texto mostrado vem da string original da API.
const paraGrafico = (texto: string): number => Number.parseFloat(texto);
const reais = (valor: unknown): string => formatarReais(Number(valor).toFixed(2));

export function Ano() {
  const ano = Number(useParams().ano);
  const valido = Number.isInteger(ano) && ano >= 1 && ano <= 9999;

  const consulta = useQuery({
    queryKey: ["ano", ano],
    enabled: valido,
    queryFn: async () => {
      const { data, error } = await api.GET("/api/anos/{ano}/resumo", { params: { path: { ano } } });
      if (!data) throw new Error(mensagemDe(error, "Não foi possível carregar o ano."));
      return data;
    },
  });

  if (!valido) return <Navigate to={`/ano/${mesAtual().ano}`} replace />;
  const dados = consulta.data;

  return (
    <section>
      <h1>Ano: {ano}</h1>
      <nav className="navegacao-mes" aria-label="Escolher ano">
        <Link to={`/ano/${ano - 1}`} rel="prev">
          ← {ano - 1}
        </Link>
        <Link to={`/ano/${ano + 1}`} rel="next">
          {ano + 1} →
        </Link>
      </nav>

      {consulta.isPending && <p role="status">Carregando…</p>}
      {consulta.isError && (
        <p role="alert" className="erro">
          {consulta.error.message}
        </p>
      )}

      {dados && dados.meses.length === 0 && <p className="aviso">Sem lançamentos em {ano}.</p>}

      {dados && dados.meses.length > 0 && (
        <>
          <table aria-label="Resumo por mês">
            <thead>
              <tr>
                <th>Mês</th>
                <th className="valor">Receitas</th>
                <th className="valor">Despesas</th>
                <th className="valor">Investimentos</th>
                <th className="valor">Saldo livre</th>
              </tr>
            </thead>
            <tbody>
              {dados.meses.map((m) => (
                <tr key={m.mes}>
                  <td>
                    <Link to={`/mes/${ano}/${m.mes}`}>{nomeDoMes(m.mes)}</Link>
                  </td>
                  <td className="valor">{formatarReais(m.receitas)}</td>
                  <td className="valor">{formatarReais(m.despesas)}</td>
                  <td className="valor">{formatarReais(m.investimentos)}</td>
                  <td className="valor">{formatarReais(m.saldo_livre)}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="graficos">
            {dados.patrimonio.length > 0 && (
              <Grafico
                titulo="Evolução do patrimônio (aportes acumulados)"
                opcoes={{
                  tooltip: { trigger: "axis", valueFormatter: reais },
                  grid: { left: 80, right: 20, top: 20, bottom: 40 },
                  xAxis: { type: "category", data: dados.patrimonio.map((p) => p.rotulo) },
                  yAxis: { type: "value", axisLabel: { formatter: reais } },
                  series: [{ type: "line", name: "Patrimônio", data: dados.patrimonio.map((p) => paraGrafico(p.valor)) }],
                }}
                dados={
                  <table aria-label="Dados da evolução do patrimônio">
                    <thead>
                      <tr>
                        <th>Mês</th>
                        <th className="valor">Acumulado</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.patrimonio.map((p) => (
                        <tr key={p.rotulo}>
                          <td>{p.rotulo}</td>
                          <td className="valor">{formatarReais(p.valor)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                }
              />
            )}
            {dados.ranking.length > 0 && (
              <Grafico
                titulo="Ranking de categorias de despesa"
                opcoes={{
                  tooltip: { trigger: "axis", valueFormatter: reais },
                  grid: { left: 140, right: 30, top: 20, bottom: 30 },
                  xAxis: { type: "value", axisLabel: { formatter: reais } },
                  yAxis: { type: "category", inverse: true, data: dados.ranking.slice(0, 10).map((r) => r.categoria) },
                  series: [{ type: "bar", name: "Total", data: dados.ranking.slice(0, 10).map((r) => paraGrafico(r.total)) }],
                }}
                dados={
                  <table aria-label="Dados do ranking de categorias">
                    <thead>
                      <tr>
                        <th>Categoria</th>
                        <th className="valor">Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.ranking.map((r) => (
                        <tr key={r.categoria}>
                          <td>{r.categoria}</td>
                          <td className="valor">{formatarReais(r.total)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                }
              />
            )}
            {dados.variacao.length > 0 && (
              <Grafico
                titulo="Variação do saldo livre entre meses"
                opcoes={{
                  tooltip: { trigger: "axis", valueFormatter: reais },
                  grid: { left: 80, right: 20, top: 20, bottom: 40 },
                  xAxis: { type: "category", data: dados.variacao.map((v) => v.rotulo), axisLabel: { hideOverlap: true } },
                  yAxis: { type: "value", axisLabel: { formatter: reais } },
                  series: [
                    {
                      type: "bar",
                      name: "Variação",
                      data: dados.variacao.map((v) => ({
                        value: paraGrafico(v.valor),
                        itemStyle: { color: v.valor.startsWith("-") ? "#a31621" : "#1b6e3c" },
                      })),
                    },
                  ],
                }}
                dados={
                  <table aria-label="Dados da variação do saldo">
                    <thead>
                      <tr>
                        <th>Mês</th>
                        <th className="valor">Variação</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.variacao.map((v) => (
                        <tr key={v.rotulo}>
                          <td>{v.rotulo}</td>
                          <td className="valor">{formatarReais(v.valor)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                }
              />
            )}
          </div>
        </>
      )}
    </section>
  );
}
