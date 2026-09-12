"""Muuk — agente A2UI sobre MCP.

Agno + Gemini. Emite respuestas estructuradas: texto + lista de componentes
del catálogo. api.py convierte esto en mensajes A2UI (createSurface /
surfaceUpdate / dataModelUpdate / deleteSurface) y lo valida siempre.
"""

import os
from pathlib import Path

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


INSTRUCTIONS = f"""
Eres Muuk, el asistente financiero de Banorte que genera interfaces vivas.

Intenciones conocidas: AHORRAR, INVERTIR, PAGAR_DEUDA, CONSULTAR_SALDO, TRANSFERIR.
Componentes disponibles: {list(CATALOG)}.

Reglas:
- Decide siempre: texto corto + componentes del catálogo. Nunca un muro de texto.
- Read-only: get_usuario, get_perfil_financiero, get_productos_usuario,
  get_resumen_gastos, simular_plan_pago, get_preferencias, get_resumen_interacciones.
  Úsalos antes de renderizar opciones numéricas.
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
"""


def build_agent(mcp_command: list[str] | None = None) -> Agent:
    cmd = mcp_command or ["python", str(Path(__file__).parent / "mcp_server.py")]
    return Agent(
        name="Muuk",
        model=Gemini(id=os.getenv("GEMINI_MODEL", "gemini-2.5-flash")),
        tools=[MCPTools(command=" ".join(cmd))],
        instructions=INSTRUCTIONS,
        output_schema=MuukResponse,
        markdown=False,
    )
