// Catálogo A2UI oficial de Muuk (v0.9): definiciones Zod + renderers React.
// Espejo de server/catalog.py — el server valida fail-closed, aquí viven las
// definiciones que el agente ve y los renderers que el usuario ve (spec A2UI).
import { z } from "zod";
import { createCatalog, useA2UIActions } from "@copilotkit/a2ui-renderer";
import { renderComponent } from "../registry";
// Side-effect imports: cada componente se registra en ../registry.
import "../../components/PlanDePago";
import "../../components/TablaGastos";
import "../../components/Confirmacion";
import "../../components/GraficaPastel";
import "../../components/GraficaBarras";
import "../../components/GraficaLinea";
import "../../components/ProgresoMeta";
import "../../components/ComandoUI";
import "../../components/TarjetaMetrica";

const info = z.string().optional(); // tarjeta al cursor (erst InfoMixin)

// ── Definiciones (Zod + descripción para el agente) — espejo de catalog.py ──
const opcionPago = z.object({ meses: z.number(), pago_mensual: z.number(), cat: z.number(), total: z.number().optional() });
const filaGasto = z.object({ concepto: z.string(), monto: z.number(), categoria: z.string() });
const etiquetaValor = z.object({ etiqueta: z.string(), valor: z.number() });

export const definitions = {
    PlanDePago: {
        description: "Plan de reestructura de deuda con opciones seleccionables y CTA de aplicación.",
        props: z.object({ mensaje: z.string(), monto_original: z.number(), opciones: z.array(opcionPago), cta: z.string().optional(), info }),
    },
    TablaGastos: {
        description: "Tabla de gastos por concepto/categoría (agregados) o dataRef para detalle directo del frontend.",
        props: z.object({ titulo: z.string(), filas: z.array(filaGasto).optional(), dataRef: z.string().optional(), info }),
    },
    Confirmacion: {
        description: "Confirmación de una acción o dato, con detalles opcionales.",
        props: z.object({ mensaje: z.string(), detalles: z.record(z.string(), z.unknown()).optional(), info }),
    },
    GraficaPastel: {
        description: "Gráfica de pastel con segmentos etiqueta/valor.",
        props: z.object({ titulo: z.string(), segmentos: z.array(etiquetaValor), info }),
    },
    GraficaBarras: {
        description: "Gráfica de barras con barras etiqueta/valor.",
        props: z.object({ titulo: z.string(), barras: z.array(etiquetaValor), info }),
    },
    GraficaLinea: {
        description: "Gráfica de línea con puntos etiqueta/valor.",
        props: z.object({ titulo: z.string(), puntos: z.array(etiquetaValor), info }),
    },
    TarjetaMetrica: {
        description: "Tarjeta métrica con valor ya formateado ($8,500 o +18.4%).",
        props: z.object({ titulo: z.string(), valor: z.string(), subtitulo: z.string().optional(), info }),
    },
    ProgresoMeta: {
        description: "Barra de progreso hacia una meta.",
        props: z.object({ titulo: z.string(), actual: z.number(), meta: z.number(), info }),
    },
    RetoFinanciero: {
        description: "Reto de gamificación con recompensa en Muuk Coins y CTA 'Aceptar reto'.",
        props: z.object({ reto_id: z.string(), titulo: z.string(), descripcion: z.string(), recompensa: z.number(), cta: z.string().optional(), info }),
    },
    ComandoUI: {
        description: "Comando local de interfaz (modo_oscuro, exportar_pdf).",
        props: z.object({ accion: z.enum(["modo_oscuro", "exportar_pdf"]), label: z.string().optional(), info }),
    },
};

// ── Renderers: delegan a los componentes existentes vía ../registry ─────────
// Cada renderer es un componente: usa useA2UIActions() para el dispatch
// (que fluye a onAction → POST /action).
const makeRenderer = (type) => {
    const R = ({ props }) => {
        const { dispatch } = useA2UIActions();
        return renderComponent({ componentType: type, componentId: "x", props }, (a) => dispatch(a));
    };
    return R;
};

export const renderers = Object.fromEntries(
    Object.keys(definitions).map((type) => [type, makeRenderer(type)])
);

export const muukCatalog = createCatalog(definitions, renderers, {
    catalogId: "muuk-catalog",
    includeBasicCatalog: true, // Column/Row/Text disponibles para el root
});
export const CATALOG_ID = "muuk-catalog";
