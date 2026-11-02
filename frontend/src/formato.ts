// Dinheiro é sempre texto decimal ("1200.50"); aqui não há aritmética com number (WEB-27).

const MESES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

export function nomeDoMes(mes: number): string {
  return MESES[mes - 1] ?? String(mes);
}

/** "1200.5" -> "R$ 1.200,50"; negativo -> "-R$ 30,00". */
export function formatarReais(texto: string): string {
  const negativo = texto.startsWith("-");
  const [inteiro, fracao = ""] = texto.replace("-", "").split(".");
  const agrupado = inteiro.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
  const centavos = (fracao + "00").slice(0, 2);
  return `${negativo ? "-" : ""}R$ ${agrupado},${centavos}`;
}

/** "12.5" -> "12,50" (para preencher campos de edição). */
export function paraCampo(texto: string): string {
  const [inteiro, fracao = ""] = texto.split(".");
  return `${inteiro},${(fracao + "00").slice(0, 2)}`;
}

export type LeituraDeDinheiro = { ok: true; valor: string } | { ok: false; erro: string };

/** Lê a digitação brasileira ("1.234,56", "1234,56", "12.5") e devolve o texto para a API ("1234.56"). */
export function lerDinheiro(entrada: string): LeituraDeDinheiro {
  const texto = entrada.trim().replace(/^R\$\s*/, "");
  if (!texto) return { ok: false, erro: "Informe um valor." };
  if (!/^\d[\d.,]*$/.test(texto)) return { ok: false, erro: "Use só números, ponto de milhar e vírgula." };

  let inteiro: string;
  let fracao = "";
  if (texto.includes(",")) {
    const partes = texto.split(",");
    if (partes.length > 2) return { ok: false, erro: "Use uma única vírgula para os centavos." };
    inteiro = partes[0].replace(/\./g, "");
    fracao = partes[1];
  } else if (/^\d{1,3}(\.\d{3})+$/.test(texto)) {
    inteiro = texto.replace(/\./g, ""); // 1.234 = mil duzentos e trinta e quatro
  } else {
    const partes = texto.split(".");
    if (partes.length > 2) return { ok: false, erro: "Valor inválido." };
    [inteiro, fracao = ""] = partes;
  }
  if (!/^\d+$/.test(inteiro) || !/^\d*$/.test(fracao)) return { ok: false, erro: "Valor inválido." };
  if (fracao.length > 2) return { ok: false, erro: "Use no máximo 2 casas decimais." };
  return { ok: true, valor: fracao ? `${inteiro}.${fracao}` : inteiro };
}

export function mesAtual(agora: Date = new Date()): { ano: number; mes: number } {
  return { ano: agora.getFullYear(), mes: agora.getMonth() + 1 };
}
