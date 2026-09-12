"""API de Muuk: SSE con mensajes A2UI + acciones de regreso.

Rutas:
  POST /chat    → SSE con A2UI (createSurface, surfaceUpdate, deleteSurface).
  POST /action  → interacción del usuario; cierra loop + memoria adaptativa.
"""

import json
import time
import uuid
from collections import defaultdict

import agent
import db
from catalog import validar_componente, new_message
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI(title="Muuk API")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"], allow_methods=["POST"], allow_headers=["*"])

_RATE_LIMIT = 10
_rate: dict[str, list[float]] = defaultdict(list)


def _check_rate(ip: str):
    now = time.time()
    hits = [t for t in _rate[ip] if now - t < 60]
    if len(hits) >= _RATE_LIMIT:
        raise HTTPException(429, "rate limit")
    _rate[ip] = hits + [now]


class ChatRequest(BaseModel):
    session_id: str
    mensaje: str
    user_id: str = "u1"


class ActionRequest(BaseModel):
    session_id: str
    componente: str
    evento: str
    payload: dict = {}
    user_id: str = "u1"


def _to_surface(session_id: str, resp) -> list[dict]:
    surface_id = f"s-{session_id}-{uuid.uuid4().hex[:6]}"
    msgs = [new_message("createSurface", surfaceId=surface_id)]
    comps = []
    for i, c in enumerate(resp.componentes):
        if validar_componente(c.type, c.props):
            comps.append({"componentId": f"c{i}", "componentType": c.type, "props": c.props})
        else:
            db.registrar_interaccion(session_id, "SYSTEM_RESPONSE", f"ui_bloqueada:{c.type}")
    if comps:
        msgs.append(new_message("surfaceUpdate", surfaceId=surface_id, components=comps))
    if resp.texto:
        msgs.append(new_message("dataModelUpdate", surfaceId=surface_id, path="/meta", value={"texto": resp.texto}))
    return msgs


def _run_agent(session_id: str, mensaje: str, user_id: str) -> list[dict]:
    historial = db.get_resumen_interacciones(session_id)
    preferencias = db.get_preferencias(user_id)
    prompt = (
        f"user_id={user_id}. "
        f"HISTORIAL: {json.dumps(historial, default=str)}. "
        f"PREFERENCIAS: {json.dumps(preferencias, default=str)}.\n\n{mensaje}"
    )
    resp = agent.build_agent().run(prompt).content
    return _to_surface(session_id, resp)


@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    _check_rate(request.client.host if request.client else "demo")
    db.registrar_interaccion(req.session_id, "USER_MESSAGE", req.mensaje)
    msgs = _run_agent(req.session_id, req.mensaje, req.user_id)

    def stream():
        for m in msgs:
            yield f"data: {json.dumps(m, default=str)}\n\n"

    return StreamingResponse(stream(), media_type="application/a2ui+json")


@app.post("/action")
def action(req: ActionRequest, request: Request):
    _check_rate(request.client.host if request.client else "demo")
    db.registrar_interaccion(req.session_id, "UI_ACTION", f"{req.componente}:{req.evento}")

    # Única escritura de negocio; exige CTA explícito del usuario.
    if req.evento == "aplicar_plan":
        p = req.payload
        result = db.aplicar_plan(
            req.user_id,
            p.get("meses", 12),
            p.get("pago_mensual", 0),
            p.get("cat", 0),
            p.get("monto_original", 0),
        )
        return {"ok": True, "plan": result}

    return {"ok": True}


@app.get("/transacciones")
def transacciones(user_id: str, request: Request, limit: int = 20):
    """Detalle crudo para el frontend. Canal separado del LLM: el agente nunca
    ve estas filas. En producción: user_id derivado del token de sesión y rol
    de BD distinto al del agente (mcp_agent no tiene SELECT en transaccion)."""
    _check_rate(request.client.host if request.client else "demo")
    return db.get_transacciones(user_id, limit)
