import { formatarReais, lerDinheiro, mesAtual, nomeDoMes, paraCampo } from "./formato";

// Spec: WEB-18
describe("formatarReais", () => {
  it.each([
    ["1200.50", "R$ 1.200,50"],
    ["0.00", "R$ 0,00"],
    ["5", "R$ 5,00"],
    ["1234567.89", "R$ 1.234.567,89"],
    ["-30.00", "-R$ 30,00"],
    ["12.5", "R$ 12,50"],
  ])("%s -> %s", (entrada, esperado) => {
    expect(formatarReais(entrada)).toBe(esperado);
  });

  it("nomes de mês em português", () => {
    expect(nomeDoMes(1)).toBe("janeiro");
    expect(nomeDoMes(3)).toBe("março");
    expect(nomeDoMes(12)).toBe("dezembro");
  });
});

// Spec: WEB-27
describe("lerDinheiro", () => {
  it.each([
    ["1.234,56", "1234.56"],
    ["1234,56", "1234.56"],
    ["1234.56", "1234.56"],
    ["12,5", "12.5"],
    ["12.5", "12.5"],
    ["1.234", "1234"],
    ["1.234.567", "1234567"],
    ["100", "100"],
    ["R$ 10,00", "10.00"],
    ["  7,05 ", "7.05"],
    ["0,01", "0.01"],
  ])("aceita %s e envia %s", (entrada, esperado) => {
    expect(lerDinheiro(entrada)).toEqual({ ok: true, valor: esperado });
  });

  it.each(["", "   ", "abc", "10,123", "1,2,3", "-5", "1e5", "10,5x"])("recusa %j", (entrada) => {
    const leitura = lerDinheiro(entrada);
    expect(leitura.ok).toBe(false);
  });

  it("explica o motivo de mais de duas casas", () => {
    expect(lerDinheiro("10,123")).toEqual({ ok: false, erro: "Use no máximo 2 casas decimais." });
  });

  it("nunca converte para number: valores grandes e com zeros mantêm o texto", () => {
    expect(lerDinheiro("12345678901234567890,10")).toEqual({ ok: true, valor: "12345678901234567890.10" });
  });

  it("paraCampo devolve a digitação brasileira para editar", () => {
    expect(paraCampo("1234.5")).toBe("1234,50");
    expect(paraCampo("7")).toBe("7,00");
  });

  it("mesAtual usa a data informada", () => {
    expect(mesAtual(new Date(2026, 10, 2))).toEqual({ ano: 2026, mes: 11 });
  });
});
