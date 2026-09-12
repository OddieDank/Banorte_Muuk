# Banorte × Muuk

Agente de IA que **construye la interfaz** en tiempo real: Utilizando → Agno → FastMCP → A2UI → TigerData.

## Correr

```bash
cd server
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # agrega GEMINI_API_KEY (y DATABASE_URL cuando haya)
uvicorn api:app --reload
```

Frontend: `cd frontend && pnpm dev` / `npm run dev`.

## Estado

- **M1 ✅** — scaffold del agente: `catalog.py`, `db.py`, `mcp_server.py`,
  `agent.py`, `api.py`, `validate_a2ui.py` (5/5). Frontend inicial.
- **M2 ✅** — alineado al esquema Tiger Data del compañero. `db.py` usa PG
  cuando `DATABASE_URL` está set, SQLite fallback para dev. Ver
  `server/schema_additions.sql` para cambios sugeridos al esquema.
- **M2.5 ✅** — privacidad por diseño: agente solo ve agregados
  (`get_resumen_gastos` sobre `transaccion_resumen`); detalle crudo por
  `GET /transacciones` directo al frontend (canal separado del LLM).
  `TablaGastos` soporta `dataRef`.
- **Siguiente: M3** — correr contra Gemini real + integrar app Next.
