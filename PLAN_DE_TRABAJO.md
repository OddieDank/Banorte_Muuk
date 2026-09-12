# Muuk — Plan de Trabajo (HackMTY 2026 × Banorte)

**Agente de IA que genera interfaces financieras vivas en tiempo real.**
Stack: Gemini · Agno · FastMCP · A2UI · Tiger Data · Next.js

> Ver detalles del reto en `presentacion.txt`.
> Este documento es la fuente de verdad entre sesiones. Actualizarlo cuando cambie una decisión.

---

## 1. Arquitectura (decidida)

```
Usuario → POST /chat (SSE, application/a2ui+json)
  → Agno Agent (Gemini) — Muuk
    ├─ MCPTools → FastMCP server
    │    ├─ get_cliente / get_saldo        (read-only)
    │    ├─ simular_plan / simular_inversion
    │    ├─ aplicar_plan                   (único con escritura, requiere confirmación)
    │    └─ registrar_interaccion          (bitácora → adaptación)
    └─ emite mensajes A2UI (createSurface / surfaceUpdate / dataModelUpdate / deleteSurface)
  → Frontend (Next.js): adapter + registry → componentes propios
  → Acción de usuario → POST /action → regresa al agente (loop cerrado)
```

**Memoria adaptativa:** cada interacción va a `interaction_log`; el prompt del agente recibe un resumen y adapta componente/preferencias. Demo-friendly, sin entrenar nada.

**Fuera de alcance:** transporte A2A, renderers oficiales A2UI, autenticación real, LangGraph.
Se agregan solo si sobra tiempo.

---

## 2. Estructura del repo

```
Banorte_Muuk/
  .gitignore
  README.md               # cómo correr (entregable #2)
  PLAN_DE_TRABAJO.md      # este archivo
  presentacion.txt
  server/
    requirements.txt
    catalog.py            # catálogo propio A2UI (schemas Pydantic por componente)
    mcp_server.py         # FastMCP: tools + validación estricta
    agent.py              # Muuk: Agno + Gemini + output_schema A2UI
    api.py                # FastAPI: /chat SSE + /action + rate limit
    db.py                 # Tiger Data + seed (la traerá el compañero de BD)
    validate_a2ui.py      # chequeo de mensajes contra el catálogo (control continuo)
  frontend/
    a2ui/adapter.ts       # parser de mensajes A2UI (subset v0.9.1)
    a2ui/registry.tsx     # type → componente React
    components/           # nuestros componentes del catálogo
  docs/architecture.md    # diagrama + tradeoffs (entregable #4)
```

---

## 3. Seguridad (no-negociable desde el día 1)

1. Pydantic en todo argumento de tool; consultas parametrizadas; sin SQL crudo.
2. `get_*` y `simular_*` read-only; `aplicar_plan` requiere evento explícito del usuario.
3. `.env` (gitignored): `GEMINI_API_KEY`, `DATABASE_URL`. `.env.example` commiteado.
4. Navegador solo habla con `/chat` y `/action`; MCP es el único con credenciales.
5. `audit_log` en Tiger Data: tool, args, timestamp, session_id.
6. Rate limit en `/chat`.
7. Datos 100% sintéticos.
8. Salida del LLM validada contra `catalog.py` antes de enviarse al frontend; componente desconocido → se bloquea y se loguea (anti UI-injection).
9. **Privacidad por diseño (implementado):** el agente solo ve agregados
   (`transaccion_resumen` / `get_resumen_gastos`); el rol `mcp_agent` no tiene
   SELECT en `transaccion` cruda. El detalle lo sirve `GET /transacciones`
   directo al frontend, canal separado del LLM. `TablaGastos` usa `dataRef`.

---

## 4. Catálogo inicial (3 componentes para el primer loop)

| Componente | Props (resumen) | Acción |
|---|---|---|
| `PlanDePago` | opciones[{meses, pago_mensual, cat}], cta | `aplicar_plan` |
| `TablaGastos` | filas[{concepto, monto, categoria}] | — (vista) |
| `Confirmacion` | mensaje, detalles | `registrar_interaccion` |

Luego: `SimuladorInversion`, `GraficaLineal`, `FormularioPrestamo` (solo si el loop 1 ya cierra).

---
## 5. Milestones (48h)

- **M1 (h 0–3) ✅** scaffold del agente: `catalog.py`, `db.py` (SQLite fallback),
  `mcp_server.py`, `agent.py`, `api.py`, `validate_a2ui.py` + frontend
  inicial (`adapter/types/registry` + `PlanDePago`). Self-check pasa (5/5).
- **M2 (h 3–6) ✅** stack alineado al esquema Tiger Data del compañero:
  `db.py` reescrito (PG + SQLite fallback), `mcp_server.py` con tools del
  esquema real, `agent.py` y `api.py` con `user_id` UUID. `schema_additions.sql`
  con 3 cambios sugeridos (montos, movimientos, plan_pago).
- **M3 (h 6–12):** correr contra Gemini real + integrar app Next con registry.
  **Loop abierto.**
- **M4 (h 12–24):** `POST /action` + `registrar_interaccion` + adaptación por historial. **Loop cerrado.**
- **M5 (h 24–36):** componentes 4–7, audit UI, preferencias persistentes.
- **M6 (h 36–48):** UX, `docs/architecture.md`, ensayo de demo.

**Demo mínima a fallar:** un flujo (plan de pago) completo, cerrado, con acción real en BD.
Sin eso, no agregar componentes.

---

## 6. Checklist por sesión

- [ ] Antes de codear: leer este plan, revisar que M-n siga vigente.
- [ ] Correr `validate_a2ui.py` antes de push (cuando exista).
- [ ] No commitear `.env`. Revisar `git status` antes de push.
- [ ] Actualizar este archivo si cambia una decisión arquitectónica.

---

## 7. Decisiones pendientes (no bloqueantes)

- Versión del spec A2UI: v0.9.1 (current) vs v1.0 (candidato). Default: v0.9.1.
- Renderer: propio (adapter slim) vs CopilotKit/ag-ui React. Default: propio.
- Si Tiger Data tarda: fallback SQLite en `db.py` con misma interfaz (compañero de BD decide).
