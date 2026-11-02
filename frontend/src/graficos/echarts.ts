// Carregado sob demanda (import dinâmico) para não pesar no início da aplicação.
import { BarChart, LineChart } from "echarts/charts";
import { GridComponent, TooltipComponent } from "echarts/components";
import * as echarts from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";

echarts.use([BarChart, LineChart, GridComponent, TooltipComponent, CanvasRenderer]);

export { echarts };
