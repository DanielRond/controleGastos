import "@testing-library/jest-dom/vitest";
import { cleanup, configure } from "@testing-library/react";
import { afterEach } from "vitest";

// CI e máquinas lentas: folga para as consultas assíncronas.
configure({ asyncUtilTimeout: 4000 });

// jsdom não implementa canvas; sem isto ele imprime "Not implemented" a cada gráfico.
HTMLCanvasElement.prototype.getContext = (() => null) as unknown as typeof HTMLCanvasElement.prototype.getContext;

afterEach(() => cleanup());
