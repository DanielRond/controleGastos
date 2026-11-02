import { defineConfig, devices } from "@playwright/test";

// Testes de ponta a ponta: navegador real contra a API de verdade servindo o front compilado.
// Antes: `npm run build`. O servidor usa SQLite temporário e a conta ana / senha-segura-123.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"]],
  use: {
    baseURL: "http://127.0.0.1:8765",
    locale: "pt-BR",
    timezoneId: "America/Sao_Paulo",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "uv run python ../scripts/servidor_e2e.py --porta 8765",
    url: "http://127.0.0.1:8765/entrar",
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },
});
