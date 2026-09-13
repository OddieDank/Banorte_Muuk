# Banorte × Muuk

Agente de IA que **genera la interfaz en tiempo real**: el usuario pregunta en lenguaje natural, el modelo decide qué componentes renderizar (gráficas, tablas, planes de pago, retos) y el frontend los pinta desde el catálogo declarado por el equipo. Nada de respuestas de solo-texto.

**Pipeline:** Usuario → Agno (Gemini) → FastMCP → ops A2UI v0.9 → AG-UI events → React renderer → Tiger Data (Timescale Cloud).

## Tecnologías reales

| Capa | Tech |
|---|---|
| Modelo | Gemini via `agno` |
| Tools | `fastmcp` (MCP) |
| Backend | FastAPI + uvicorn, `ag-ui-protocol` (AG-UI events), `ag-ui-a2ui-toolkit` (ops A2UI) |
| Frontend | React 19 + Vite, `@ag-ui/client` transporte, `@copilotkit/a2ui-renderer` (render oficial a2ui), Zod |
| DB | Tiger Data (Timescale Cloud) via `psycopg2` |
| Voz | ElevenLabs (TTS/STT) opcional |

## Arquitectura (resumen)

- `server/agent.py` — Agno + Gemini + MCP tools; el prompt restringe componentes al catálogo.
- `server/catalog.py` — validación fail-closed del agente (anti UI-injection).
- `server/a2ui_stream.py` — componentes validados → ops v0.9 (`createSurface`/`updateComponents`/`updateDataModel`) envueltas en eventos AG-UI (`ACTIVITY_SNAPSHOT`, `TEXT`, `CUSTOM`).
- `server/api.py` — `POST /chat` = stream AG-UI SSE; `POST /action` = acciones del usuario (única ruta que escribe en DB).
- `server/mcp_server.py` — tools FastMCP (lectura de agregados; `aplicar_plan` y `registrar_interaccion` también expuestas por compat).
- `server/db.py` — Tiger Data; el agente solo ve agregados (`transaccion_resumen`), detalle crudo va directo al frontend por GET.
- `frontend/src/muuk/MuukChat.jsx` — parsea AG-UI SSE, alimenta `useA2UI().processMessages(ops)`, renderiza `<A2UIRenderer>`.
- `frontend/src/lib/a2ui/muukCatalog.jsx` — catálogo declarado: definiciones Zod + renderers que delegan a los componentes de `src/components/`.
- `frontend/src/components/*.tsx` — 10 componentes renderizables (PlanDePago, TablaGastos, Confirmacion, GraficaPastel/Barras/Linea, TarjetaMetrica, ProgresoMeta, ComandoUI, RetoFinanciero).
- `frontend/src/lib/api.js` — `API_URL` única con fallback localhost.

## Cómo correrlo

### 1. Backend

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # GEMINI_API_KEY, GEMINI_MODEL, DATABASE_URL
uvicorn api:app --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev            # http://localhost:5173
```

### 3. Probar

1. Login con cualquier nombre (demo, sin auth real).
2. Preguntas útiles: `¿en qué gasto más?` → gráficas reales de DB; `quiero pagar mi tarjeta` → PlanDePago; `¿mis retos?` → gamificación.
3. `Aplicar plan` y `Aceptar reto` son las únicas rutas de escritura y pasan por `/action`.

## Validación antes de push

```bash
cd server && .venv/bin/python validate_a2ui.py   # 5/5 fixtures
```

## Deploy (Vercel + backend)

- Front: cualquier platform que corra `npm run build` en `frontend/`. `VITE_API_URL` apunta al backend.
- Back: servir uvicorn con las env reales. Ojo: sin redeploy del back el front nuevo no habla A2UI.
- Ambos compañeros y A2UI coexisten porque el merge ya está cerrado en `main`.

## Chequeo rápido del pipeline A2UI

`AG-UI`: eventos `RUN_STARTED → ACTIVITY_SNAPSHOT (a2ui-surface) → CUSTOM → RUN_FINISHED` con `a2ui_operations` listas. El renderer copilotkit las valida contra el catálogo `muuk-catalog` (BYOC) y dibuja; "catálogo desconocido" es inmediato, no una tarjeta vacía.
