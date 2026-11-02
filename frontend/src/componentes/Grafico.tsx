import { useEffect, useRef, type ReactNode } from "react";

type Opcoes = Record<string, unknown>;

interface Props {
  titulo: string;
  opcoes: Opcoes;
  /** Alternativa em texto do gráfico (tabela de dados). */
  dados: ReactNode;
}

/** Sem canvas (jsdom, navegadores muito restritos) o gráfico não é desenhado, mas a tabela de dados continua. */
function suportaCanvas(): boolean {
  try {
    return !!document.createElement("canvas").getContext?.("2d");
  } catch {
    return false;
  }
}

export function Grafico({ titulo, opcoes, dados }: Props) {
  const area = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelado = false;
    let grafico: { setOption: (o: Opcoes) => void; resize: () => void; dispose: () => void } | undefined;
    const redimensionar = () => grafico?.resize();
    if (!suportaCanvas()) return undefined;
    void import("../graficos/echarts").then(({ echarts }) => {
      if (cancelado || !area.current) return;
      grafico = echarts.init(area.current);
      grafico.setOption(opcoes);
    });
    window.addEventListener("resize", redimensionar);
    return () => {
      cancelado = true;
      window.removeEventListener("resize", redimensionar);
      grafico?.dispose();
    };
  }, [opcoes]);

  return (
    <figure className="grafico-figura">
      <figcaption>
        <h3>{titulo}</h3>
      </figcaption>
      <div ref={area} role="img" aria-label={titulo} className="grafico" />
      <details>
        <summary>Ver os dados de “{titulo}” em tabela</summary>
        {dados}
      </details>
    </figure>
  );
}
