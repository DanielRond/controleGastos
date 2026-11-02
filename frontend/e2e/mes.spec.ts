import { expect, test } from "@playwright/test";
import { entrar, lancar } from "./apoio";

// Usa março de 2031 para não se misturar com os outros arquivos de teste.
const MES = "/mes/2031/3";

test.describe.configure({ mode: "serial" });

// Spec: WEB-22, WEB-27
test("lançar despesa, receita e investimento atualiza totais, classes e meta", async ({ page }) => {
  await entrar(page, MES);
  await expect(page.getByText("Nenhum lançamento neste mês.")).toBeVisible();

  await lancar(page, { descricao: "Mercado", dia: 3, valor: "1.234,56", categoria: "alimentacao" });
  await page.getByRole("button", { name: "Adicionar" }).click();
  await expect(page.getByRole("cell", { name: "R$ 1.234,56" })).toBeVisible();

  await lancar(page, { tipo: "Receita", descricao: "Freela", dia: 5, valor: "2000" });
  await page.getByRole("button", { name: "Adicionar" }).click();

  await lancar(page, { tipo: "Investimento", descricao: "Aporte", dia: 10, valor: "300,25" });
  await page.getByLabel("Classe do investimento").selectOption({ label: "Fundos imobiliários (FII)" });
  await page.getByLabel(/Ativo/).fill("KNSC11");
  await page.getByRole("button", { name: "Adicionar" }).click();

  const resumo = page.getByRole("region", { name: "Resumo do mês" });
  await expect(resumo.getByText("R$ 2.000,00")).toBeVisible();
  await expect(resumo.getByText("R$ 1.234,56")).toBeVisible();
  await expect(resumo.getByText("R$ 300,25").first()).toBeVisible();
  await expect(resumo.getByText("R$ 465,19")).toBeVisible(); // saldo: 2000,00 - 1234,56 - 300,25
  await expect(resumo.getByRole("table", { name: "Investimentos por classe" })).toContainText("100,00%");
});

// Spec: WEB-23
test("salário e meta entram nos totais e a meta mostra quanto falta; limpar remove", async ({ page }) => {
  await entrar(page, MES);

  await page.getByLabel("Salário (R$)").fill("5.000,00");
  await page.getByLabel("Meta de investimento (R$)").fill("1000");
  await page.getByRole("button", { name: "Salvar", exact: true }).click();

  await expect(page.getByText("Salário e meta salvos.")).toBeVisible();
  const resumo = page.getByRole("region", { name: "Resumo do mês" });
  await expect(resumo.getByText("R$ 7.000,00")).toBeVisible(); // 5000 de salário + 2000 de freela
  await expect(resumo.getByText(/Faltam R\$ 699,75/)).toBeVisible();

  await page.getByLabel("Salário (R$)").fill("");
  await page.getByRole("button", { name: "Salvar", exact: true }).click();
  await expect(resumo.getByText("R$ 2.000,00").first()).toBeVisible();
});

// Spec: WEB-22, WEB-08
test("o servidor recusa dia inválido e o erro aparece junto ao campo", async ({ page }) => {
  await entrar(page, MES);
  await lancar(page, { descricao: "Dia impossível", dia: 32, valor: "10" });
  await page.getByRole("button", { name: "Adicionar" }).click();

  const campo = page.getByLabel("Dia", { exact: true });
  await expect(campo).toHaveAttribute("aria-invalid", "true");
  await expect(page.getByRole("alert").filter({ hasText: "dia 32 é inválido" })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Dia impossível", exact: true })).toHaveCount(0);
});

// Spec: WEB-27
test("mais de duas casas decimais é recusado antes de enviar", async ({ page }) => {
  await entrar(page, MES);
  await lancar(page, { descricao: "Três casas", dia: 4, valor: "10,123" });
  await page.getByRole("button", { name: "Adicionar" }).click();
  await expect(page.getByRole("alert")).toHaveText("Use no máximo 2 casas decimais.");
});

// Spec: WEB-22, WEB-25
test("editar, apagar para a lixeira, restaurar e excluir definitivamente", async ({ page }) => {
  await entrar(page, MES);

  await page.getByRole("button", { name: "Editar Mercado" }).click();
  await page.getByLabel("Descrição").fill("Feira");
  await page.getByRole("button", { name: "Salvar alterações" }).click();
  await expect(page.getByRole("cell", { name: "Feira", exact: true })).toBeVisible();
  await expect(page.getByRole("cell", { name: "Mercado", exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Apagar Feira" }).click();
  await expect(page.getByText(/"Feira" foi movido para a lixeira/)).toBeVisible();
  await expect(page.getByRole("cell", { name: "Feira", exact: true })).toHaveCount(0);

  await page.getByRole("link", { name: "Abrir a lixeira" }).click();
  await expect(page.getByRole("table", { name: "Itens da lixeira" })).toContainText("Feira");

  await page.getByRole("button", { name: "Restaurar Feira" }).click();
  await expect(page.getByText('"Feira" foi restaurado.')).toBeVisible();

  await page.goto(MES);
  await expect(page.getByRole("cell", { name: "Feira", exact: true })).toBeVisible();

  await page.getByRole("button", { name: "Apagar Freela" }).click();
  await page.getByRole("link", { name: "Abrir a lixeira" }).click();
  await page.getByRole("button", { name: "Excluir definitivamente Freela" }).click();
  const dialogo = page.getByRole("alertdialog");
  await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await dialogo.getByRole("button", { name: "Excluir agora" }).click();
  await expect(page.getByText('"Freela" foi excluído definitivamente.')).toBeVisible();
  await expect(page.getByText("A lixeira está vazia.")).toBeVisible();
});

// Spec: WEB-22
test("navegar entre meses pelos links", async ({ page }) => {
  await entrar(page, MES);
  await page.getByRole("link", { name: /abril de 2031/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Mês: abril de 2031" })).toBeVisible();
  await page.getByRole("link", { name: /março de 2031/ }).click();
  await expect(page.getByRole("heading", { level: 1, name: "Mês: março de 2031" })).toBeVisible();
});
