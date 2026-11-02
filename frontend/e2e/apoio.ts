import { expect, type Page } from "@playwright/test";

export const SENHA = "senha-segura-123";

/** Entra com a conta de teste e espera chegar ao destino. */
export async function entrar(page: Page, destino = "/"): Promise<void> {
  await page.goto(destino);
  await page.getByLabel("Usuário").fill("ana");
  await page.getByLabel("Senha").fill(SENHA);
  await page.getByRole("button", { name: "Entrar" }).click();
  await expect(page.getByRole("button", { name: "Sair" })).toBeVisible();
}

export async function lancar(
  page: Page,
  { tipo = "Despesa", dia, descricao, valor, categoria }: { tipo?: string; dia: number; descricao: string; valor: string; categoria?: string },
): Promise<void> {
  await page.getByLabel("Tipo", { exact: true }).selectOption({ label: tipo });
  await page.getByLabel("Dia", { exact: true }).fill(String(dia));
  await page.getByLabel("Descrição").fill(descricao);
  await page.getByLabel("Valor (R$)").fill(valor);
  if (categoria) await page.getByLabel("Categoria").fill(categoria);
}
