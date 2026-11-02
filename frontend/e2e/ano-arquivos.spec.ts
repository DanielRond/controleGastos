import { expect, test } from "@playwright/test";
import { readFileSync } from "node:fs";
import { entrar } from "./apoio";

test.describe.configure({ mode: "serial" });

// Dois meses de 2032, com receita, despesas e investimento, para haver patrimônio, ranking e variação.
const documento = {
  anos: [
    {
      ano: 2032,
      meses: [
        {
          mes: 1,
          salario: 3000,
          meta_investimento: 500,
          despesas: [
            { descricao: "Aluguel", valor: 1200, dia: 5, categoria: "moradia" },
            { descricao: "Mercado", valor: 450.5, dia: 8, categoria: "alimentacao" },
          ],
          investimentos: [{ tipo: "renda_fixa", ativo: "CDI", descricao: "Reserva", valor: 400, dia: 10 }],
        },
        {
          mes: 2,
          salario: 3000,
          despesas: [{ descricao: "Aluguel", valor: 1200, dia: 5, categoria: "moradia" }],
          investimentos: [{ tipo: "cripto", ativo: "BTC", descricao: "Compra", valor: 150, dia: 12 }],
        },
      ],
    },
  ],
};
const arquivo = { name: "dados-2032.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(documento)) };

// Spec: WEB-26
test("importar JSON mostra quantos lançamentos foram criados", async ({ page }) => {
  await entrar(page, "/arquivos");
  await page.getByLabel("Arquivo JSON").setInputFiles(arquivo);
  await expect(page.getByText(/5 lançamentos criados \(2032-01, 2032-02\)/)).toBeVisible();
});

// Spec: WEB-26
test("importar de novo avisa do conflito e só substitui depois de confirmar", async ({ page }) => {
  await entrar(page, "/arquivos");
  await page.getByLabel("Arquivo JSON").setInputFiles(arquivo);

  const aviso = page.getByRole("alert");
  await expect(aviso).toContainText("já existem dados nos meses: 2032-01, 2032-02");
  await aviso.getByRole("button", { name: "Substituir os meses do arquivo" }).click();
  const dialogo = page.getByRole("alertdialog");
  await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await dialogo.getByRole("button", { name: "Substituir agora" }).click();

  await expect(page.getByText(/5 lançamentos criados/)).toBeVisible();
  await expect(page.getByText(/5 lançamentos antigos foram para a lixeira/)).toBeVisible();
});

// Spec: WEB-26
test("arquivo inválido mostra os erros com caminho e não importa nada", async ({ page }) => {
  await entrar(page, "/arquivos");
  const ruim = { anos: [{ ano: 2033, meses: [{ mes: 13 }, { mes: 1, despesas: [{ descricao: "x", valor: 1, dia: 40 }] }] }] };
  await page.getByLabel("Arquivo JSON").setInputFiles({ name: "ruim.json", mimeType: "application/json", buffer: Buffer.from(JSON.stringify(ruim)) });

  const alerta = page.getByRole("alert");
  await expect(alerta).toContainText("2 erro(s) e nada foi importado");
  await expect(alerta).toContainText("anos[0].meses[0].mes");
  await expect(alerta).toContainText("anos[0].meses[1].despesas[0].dia");
});

// Spec: WEB-24
test("tela do ano mostra o resumo e desenha os três gráficos num canvas de verdade", async ({ page }) => {
  await entrar(page, "/ano/2032");

  const tabela = page.getByRole("table", { name: "Resumo por mês" });
  await expect(tabela).toContainText("janeiro");
  await expect(tabela).toContainText("R$ 3.000,00");
  await expect(tabela).toContainText("fevereiro");

  for (const nome of ["Evolução do patrimônio (aportes acumulados)", "Ranking de categorias de despesa", "Variação do saldo livre entre meses"]) {
    const grafico = page.getByRole("img", { name: nome });
    await expect(grafico.locator("canvas")).toBeVisible();
    const caixa = await grafico.locator("canvas").boundingBox();
    expect(caixa?.width ?? 0).toBeGreaterThan(200);
    expect(caixa?.height ?? 0).toBeGreaterThan(100);
  }

  await page.getByText(/Ver os dados de “Ranking/).click();
  await page.getByText(/Ver os dados de “Evolução do patrimônio/).click();
  await expect(page.getByRole("table", { name: "Dados do ranking de categorias" })).toContainText("moradia");
  await expect(page.getByRole("table", { name: "Dados da evolução do patrimônio" })).toContainText("R$ 550,00"); // 400 + 150 acumulados
});

// Spec: WEB-24
test("ano sem dados mostra um aviso", async ({ page }) => {
  await entrar(page, "/ano/1999");
  await expect(page.getByText("Sem lançamentos em 1999.")).toBeVisible();
});

// Spec: WEB-26
test("baixar planilha, CSV e JSON entrega arquivos de verdade", async ({ page }) => {
  await entrar(page, "/arquivos");

  const baixar = async (nome: string) => {
    const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: nome }).click()]);
    const caminho = await download.path();
    return { nome: download.suggestedFilename(), bytes: readFileSync(caminho) };
  };

  const xlsx = await baixar("Baixar planilha (.xlsx)");
  expect(xlsx.nome).toBe("controlegastos-todos.xlsx");
  expect(xlsx.bytes.subarray(0, 2).toString()).toBe("PK");

  const csv = await baixar("Baixar CSV (.zip)");
  expect(csv.nome).toBe("controlegastos-todos.zip");
  expect(csv.bytes.subarray(0, 2).toString()).toBe("PK");

  const json = await baixar("Exportar JSON");
  expect(json.nome).toBe("controlegastos-todos.json");
  expect(JSON.parse(json.bytes.toString("utf-8")).anos.some((a: { ano: number }) => a.ano === 2032)).toBe(true);
});

// Spec: WEB-26
test("baixar só um ano limita o arquivo", async ({ page }) => {
  await entrar(page, "/arquivos");
  await page.getByLabel("Um ano").check();
  await page.getByLabel("Ano", { exact: true }).fill("2032");

  const [download] = await Promise.all([page.waitForEvent("download"), page.getByRole("link", { name: "Exportar JSON" }).click()]);
  expect(download.suggestedFilename()).toBe("controlegastos-2032.json");
  const conteudo = JSON.parse(readFileSync(await download.path(), "utf-8"));
  expect(conteudo.anos.map((a: { ano: number }) => a.ano)).toEqual([2032]);
});

// Spec: WEB-25
test("esvaziar a lixeira pede confirmação e remove tudo", async ({ page }) => {
  await entrar(page, "/lixeira");
  await expect(page.getByRole("table", { name: "Itens da lixeira" })).toContainText("Aluguel"); // vindos da substituição

  await page.getByRole("button", { name: "Esvaziar lixeira" }).click();
  await page.getByRole("alertdialog").getByRole("button", { name: "Esvaziar agora" }).click();
  await expect(page.getByText(/foram excluídos definitivamente/)).toBeVisible();
  await expect(page.getByText("A lixeira está vazia.")).toBeVisible();
});

// Spec: WEB-18
test("a tela de arquivos é navegável por teclado, com todos os campos rotulados", async ({ page }) => {
  await entrar(page, "/arquivos");
  await expect(page.getByLabel("Todos os anos")).toBeVisible();
  await expect(page.getByLabel("Um ano")).toBeVisible();
  await expect(page.getByLabel("Arquivo JSON")).toBeVisible();

  await page.getByLabel("Todos os anos").focus();
  await page.keyboard.press("Tab");
  // do primeiro radio segue para os links de download, sem armadilhas de foco
  const alvo = await page.evaluate(() => document.activeElement?.tagName);
  expect(["INPUT", "A"]).toContain(alvo);
});
