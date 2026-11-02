import { expect, test } from "@playwright/test";
import { entrar, SENHA } from "./apoio";

// Spec: WEB-21, WEB-20
test("rota protegida leva ao login e, depois de entrar, volta para onde a pessoa queria", async ({ page }) => {
  await page.goto("/lixeira");
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();

  await page.getByLabel("Usuário").fill("ana");
  await page.getByLabel("Senha").fill(SENHA);
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("heading", { name: "Lixeira" })).toBeVisible();
  await expect(page).toHaveURL(/\/lixeira$/);
});

// Spec: WEB-20
test("senha errada mostra uma mensagem genérica e anunciada", async ({ page }) => {
  await page.goto("/entrar");
  await page.getByLabel("Usuário").fill("ana");
  await page.getByLabel("Senha").fill("senha-errada-123");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page.getByRole("alert")).toHaveText("Usuário ou senha inválidos.");
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
});

// Spec: WEB-20
test("entrar abre o mês atual", async ({ page }) => {
  await entrar(page, "/entrar");
  const agora = new Date();
  await expect(page).toHaveURL(new RegExp(`/mes/${agora.getFullYear()}/${agora.getMonth() + 1}$`));
  await expect(page.getByRole("heading", { level: 1, name: /^Mês:/ })).toBeVisible();
});

// Spec: WEB-21
test("o cabeçalho tem os links e Sair encerra a sessão de verdade", async ({ page }) => {
  await entrar(page);
  const nav = page.getByRole("navigation", { name: "Principal" });
  for (const nome of ["Mês", "Ano", "Lixeira", "Arquivos"]) await expect(nav.getByRole("link", { name: nome })).toBeVisible();

  await page.getByRole("button", { name: "Sair" }).click();
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();

  await page.goto("/arquivos"); // a sessão acabou: o cookie não vale mais
  await expect(page.getByRole("heading", { name: "Entrar" })).toBeVisible();
});

// Spec: WEB-18, WEB-20
test("dá para entrar só com o teclado, na ordem usuário, senha, botão", async ({ page }) => {
  await page.goto("/entrar");
  await expect(page.getByLabel("Usuário")).toBeFocused();
  await page.keyboard.type("ana");
  await page.keyboard.press("Tab");
  await expect(page.getByLabel("Senha")).toBeFocused();
  await page.keyboard.type(SENHA);
  await page.keyboard.press("Tab");
  await expect(page.getByRole("button", { name: "Entrar" })).toBeFocused();
  await page.keyboard.press("Enter");

  await expect(page.getByRole("button", { name: "Sair" })).toBeVisible();
});
