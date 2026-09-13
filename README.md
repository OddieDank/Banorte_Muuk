# Banorte × Muuk

Agente de IA que **construye la interfaz** en tiempo real: Usuario → Agno (Gemini) → FastMCP → **A2UI v0.9 oficial sobre AG-UI** → Tiger Data (Timescale Cloud). Render: `@copilotkit/a2ui-renderer` (React), catálogo BYOC con Zod.

## Cómo correrlo (desde cero)

### 1. Clonar y backend

```bash
git clone https://github.com/OddieDank/Banorte_Muuk.git
cd Banorte_Muuk/server

python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
```

Edita `server/.env` con estos tres valores (pídele al equipo la API key y la URL de la DB, o copia el `.env` de alguien del equipo):

```
GEMINI_API_KEY=<key de AI Studio, empieza con AIza>
GEMINI_MODEL=gemini-3.5-flash-lite
DATABASE_URL=postgresql://...tsdb.cloud.timescale.com...?sslmode=require
```

> `GEMINI_MODEL` importa: `gemini-2.5-flash` está bloqueado para cuentas nuevas
> y `gemini-3.6-flash` tiene límite gratis de 20 requests/día. El lite aguanta la demo.

Levanta el backend:

```bash
uvicorn api:app --port 8000
```

### 2. Frontend (otra terminal)

```bash
cd Banorte_Muuk/frontend
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev            # http://localhost:5173
```

### 3. Probar

1. Abre http://localhost:5173 → login con cualquier nombre (demo, sin auth real).
2. En la barra de búsqueda pregunta, por ejemplo:
   - `quiero pagar la deuda de mi tarjeta` → aparece **PlanDePago** con opciones reales
   - `¿en qué gasto más?` → aparece **TablaGastos** con tus categorías
   - `¿cuál es mi saldo?` → tus productos
3. El botón **Aplicar plan** del PlanDePago pega a `POST /action` y persiste en la DB (tabla `plan_pago`).

### Troubleshooting

| Síntoma | Causa | Fix |
|---|---|---|
| `DATABASE_URL no está definida` | falta en `.env` | ver paso 1 |
| 401 de Gemini | key inválida u OAuth token | genera una en https://aistudio.google.com/apikey |
| 404 "model no longer available" | modelo viejo en `.env` | `GEMINI_MODEL=gemini-3.5-flash-lite` |
| 429 RESOURCE_EXHAUSTED | cuota diaria free | espera o habilita billing |
| 503 UNAVAILABLE | saturación temporal de Google | reintenta en unos segundos |
| CORS en el navegador | front en puerto ≠5173 | agregar origen en `server/api.py` |

## Arquitectura (resumen)

- `server/catalog.py` — únicos componentes que el agente puede renderizar (fail-closed, anti UI-injection); el frontend espeja el catálogo con Zod.
- `server/a2ui_stream.py` — componentes validados → ops A2UI v0.9 oficiales (`createSurface`/`updateComponents`/`updateDataModel`) envueltas en eventos AG-UI (`ACTIVITY_SNAPSHOT` a2ui-surface + TEXT/CUSTOM).
- `server/mcp_server.py` — tools FastMCP; solo `aplicar_plan` escribe y requiere confirmación.
- `server/agent.py` — Agno + Gemini; ruteo de intención por keywords + JSON parse robusto.
- `server/db.py` — Tiger Data (PG-only); privacidad: el agente solo ve agregados (`transaccion_resumen`), el detalle crudo va directo al frontend por `GET /transacciones`.
- `frontend/src/muuk/MuukChat.jsx` — stream AG-UI → `useA2UI().processMessages()` → `<A2UIRenderer>`; onAction → `POST /action`.
- `frontend/src/lib/a2ui/muukCatalog.jsx` — catálogo oficial: definiciones Zod + renderers (BYOC) vía `@copilotkit/a2ui-renderer`, id `muuk-catalog`.
- `frontend/src/lib/registry.jsx` — registry interno al que delegan los renderers (los 10 componentes de `src/components/`), con tooltip `info`.

Chequeo antes de push: `cd server && .venv/bin/python validate_a2ui.py` (5/5).
