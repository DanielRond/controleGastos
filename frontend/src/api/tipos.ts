import type { components } from "./schema";

export type Lancamento = components["schemas"]["Lancamento"];
export type MesSaida = components["schemas"]["MesSaida"];
export type AnoSaida = components["schemas"]["AnoSaida"];
export type TipoDeLancamento = components["schemas"]["LancamentoEntrada"]["tipo"];

export const TIPOS_DE_INVESTIMENTO: { valor: string; rotulo: string }[] = [
  { valor: "renda_fixa", rotulo: "Renda fixa" },
  { valor: "fii", rotulo: "Fundos imobiliários (FII)" },
  { valor: "cripto", rotulo: "Criptomoedas" },
];

export function rotuloDaClasse(tipo: string): string {
  return TIPOS_DE_INVESTIMENTO.find((t) => t.valor === tipo)?.rotulo ?? tipo;
}
