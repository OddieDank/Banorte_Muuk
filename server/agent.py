"""Muuk — agente A2UI sobre MCP.

Agno + Gemini. Emite respuestas estructuradas: texto + lista de componentes
del catálogo. api.py convierte esto en mensajes A2UI (createSurface /
surfaceUpdate / dataModelUpdate / deleteSurface) y lo valida siempre.
"""

import asyncio
import json
import os
import sys
import threading
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.mcp import MCPTools
from catalog import CATALOG
from pydantic import BaseModel


class Componente(BaseModel):
    type: str = next(iter(CATALOG))
    props: dict


class MuukResponse(BaseModel):
    texto: str
    componentes: list[Componente]


_SCHEMAS = json.dumps(
    {nombre: schema.model_json_schema() for nombre, schema in CATALOG.items()},
    ensure_ascii=False,
)

INSTRUCTIONS = f"""
Eres Muuk, el asistente financiero de Banorte que genera interfaces vivas.

Intenciones conocidas: AHORRAR, INVERTIR, PAGAR_DEUDA, CONSULTAR_SALDO, TRANSFERIR.
Componentes disponibles y sus props EXACTAS (respeta nombres y tipos, no inventes otras):
{_SCHEMAS}

Reglas:
- Decide siempre: texto corto + componentes del catálogo. Nunca un muro de texto.
- Ruteo OBLIGATORIO por intención:
  · gastos/categorías/"en qué gasto"/análisis de consumo → get_resumen_gastos + TablaGastos.
  · deuda/pagar/plazos/tarjeta/reestructura → simular_plan_pago + PlanDePago.
  · saldo/cuentas/productos → get_productos_usuario + TablaGastos.
  No uses PlanDePago si el usuario no habló de deuda o pagos.
- Read-only: get_usuario, get_perfil_financiero, get_productos_usuario,
  get_resumen_gastos, simular_plan_pago, get_preferencias, get_resumen_interacciones.
  OBLIGATORIO: antes de renderizar PlanDePago llama simular_plan_pago y usa sus
  cifras exactas (pago_mensual, cat). NUNCA inventes montos ni tasas.
- Privacidad: solo ves agregados de gasto, nunca transacciones crudas. En
  TablaGastos usa props con dataRef (p. ej. "/api/transacciones").
- NUNCA llamas `aplicar_plan` salvo que el mensaje del usuario haya sido generado
  por un clic explícito en CTA (api.py lo hace en /action; aquí no).
- Adaptación: si recibes CONTEXTO DEL USUARIO (perfil, productos, gastos,
  preferencias), usa esos datos para personalizar el componente y su orden.
  Si el usuario prefiere tablas, usa TablaGastos; si elige la opción más corta,
  preordena así. Si no hay preferencias, decide por el perfil financiero.
- Registra qué funcionó: cuando el usuario interactúa con un componente, usa
  actualizar_preferencia(intencion_nombre, componente_nombre, success).
- Eres banca: cifras claras, CAT visible, sin modismos coloquiales abusivos.

FORMATO DE RESPUESTA (obligatorio):
Responde SOLO con JSON válido, sin markdown ni texto extra:
{{"texto": "mensaje corto para el usuario",
  "componentes": [{{"type": "<tipo del catálogo>", "props": {{...}}}}]}}
"""


def build_agent(mcp_command: list[str] | None = None) -> Agent:
    cmd = mcp_command or [sys.executable, str(Path(__file__).parent / "mcp_server.py")]
    return Agent(
        name="Muuk",
        model=Gemini(id=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"), api_key=os.getenv("GEMINI_API_KEY")),
        tools=[MCPTools(command=" ".join(cmd))],
        instructions=INSTRUCTIONS,
        markdown=False,
    )


# Router determinista por keywords: el modelo lite no siempre obedece la regla
# de ruteo del prompt, así que la intención se detecta en código y se inyecta.
_RUTAS = [
    (("gasto", "gastos", "consumo", "categoría", "categoria"),
     "CONSULTAR_GASTOS → llama get_resumen_gastos y responde con TablaGastos"),
    (("deuda", "pagar", "plazo", "tarjeta", "reestructura", "meses"),
     "PAGAR_DEUDA → llama simular_plan_pago y responde con PlanDePago"),
    (("saldo", "cuenta", "producto", "inversión", "inversion"),
     "CONSULTAR_SALDO → llama get_productos_usuario y responde con TablaGastos"),
]


def _hint_intencion(prompt: str) -> str:
    low = prompt.lower()
    for keywords, ruta in _RUTAS:
        if any(k in low for k in keywords):
            return f"\nINTENCIÓN DETECTADA (obligatoria, no la cambies): {ruta}."
    return ""


# Un solo agente + una sola conexión MCP para todo el proceso: reconectar por
# request levantaba un servidor MCP nuevo (boot de varios segundos por mensaje).
_LOOP = asyncio.new_event_loop()
_LOCK = threading.Lock()
_AGENT: Agent | None = None


def _get_agent() -> Agent:
    global _AGENT
    if _AGENT is None:
        _AGENT = build_agent()
        _LOOP.run_until_complete(_AGENT.tools[0].connect())
    return _AGENT


def run_muuk(prompt: str, mcp_command: list[str] | None = None) -> MuukResponse:
    """Corre el agente y parsea su JSON. output_schema no se usa: Gemini
    Developer API rechaza `props: dict` (additionalProperties).
    Async: agno 3.x solo conecta MCPTools en arun(), no en run() sync."""
    with _LOCK:  # FastAPI corre endpoints sync en threadpool; un loop a la vez
        raw = _LOOP.run_until_complete(_get_agent().arun(prompt + _hint_intencion(prompt))).content
    if not isinstance(raw, str):
        raw = getattr(raw, "text", None) or str(raw)
    try:
        data = json.loads(raw[raw.index("{"):raw.rindex("}") + 1], strict=False)
        return MuukResponse.model_validate(data)
    except Exception as e:
        print(f"[run_muuk] parse falló ({type(e).__name__}: {e}); raw[:200]={raw[:200]!r}")
        return MuukResponse(texto=str(raw), componentes=[])
