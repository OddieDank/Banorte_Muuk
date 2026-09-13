"""Servidor MCP de Muuk (FastMCP): datos, herramientas y acciones.

Todas las tools validan y toda tool mutadora escribe audit_log.
`aplicar_plan` solo existe como tool de escritura; el agente no lo llama sin
que api.py confirme la interacción del usuario (ver /action).
"""

import db
from fastmcp import FastMCP

mcp = FastMCP("muuk")


# ── Read-only ─────────────────────────────────────────────────────────────

@mcp.tool
def get_usuario(user_id: str) -> dict:
    """Datos básicos del usuario. Read-only."""
    return db.get_usuario(user_id) or {"error": "usuario no encontrado"}


@mcp.tool
def get_perfil_financiero(user_id: str) -> dict:
    """Perfil financiero: ingreso, ahorro, deuda, meta. Read-only."""
    return db.get_perfil_financiero(user_id) or {"error": "perfil no encontrado"}


@mcp.tool
def get_productos_usuario(user_id: str) -> list:
    """Productos del usuario con saldos y deudas. Read-only."""
    return db.get_productos_usuario(user_id)


@mcp.tool
def get_resumen_gastos(user_id: str, meses: int = 3) -> list:
    """Agregados de gasto por categoría/mes. Read-only.
    Privacidad: el agente NUNCA ve transacciones crudas, solo agregados."""
    return db.get_resumen_gastos(user_id, meses)


@mcp.tool
def get_presupuesto_estimado(user_id: str) -> list:
    """Semáforo de presupuesto por categoría: promedio histórico vs mes actual.
    Read-only; estado: sobre / al_limite / bajo."""
    return db.get_presupuesto_estimado(user_id)


@mcp.tool
def simular_plan_pago(user_id: str, cat: float, meses: int = 12) -> dict:
    """Simula reestructura de deuda. Read-only.
    Devuelve monto_original (deuda real) y varias opciones de plazo:
    12/18/24 meses (más el plazo pedido si es distinto), CAT escalonado."""
    productos = db.get_productos_usuario(user_id)
    deuda = next((p for p in productos if p.get("deuda_actual") and p["deuda_actual"] > 0), None)
    if not deuda:
        return {"error": "sin deuda activa"}
    monto = deuda["deuda_actual"]
    plazos = sorted({12, 18, 24, meses})
    opciones = [
        {**db.simular_plan_pago(monto, m, round(cat + (m - 12) / 6 * 1.5, 1))}
        for m in plazos
    ]
    return {"monto_original": monto, "opciones": opciones}


@mcp.tool
def get_preferencias(user_id: str, intencion_id: str | None = None) -> list:
    """Preferencias de UI del usuario (aprendizaje). Read-only."""
    return db.get_preferencias(user_id, intencion_id)


@mcp.tool
def get_resumen_interacciones(sesion_id: str) -> list:
    """Historial reciente de la sesión: contexto para adaptación."""
    return db.get_resumen_interacciones(sesion_id)


# ── Escritura (audit + confirmación) ──────────────────────────────────────

@mcp.tool
def aplicar_plan(user_id: str, meses: int, pago_mensual: float, cat: float, monto_original: float) -> dict:
    """Aplica un plan de pago. SOLO tras confirmación explícita del usuario."""
    return db.aplicar_plan(user_id, meses, pago_mensual, cat, monto_original)


@mcp.tool
def registrar_interaccion(sesion_id: str, tipo: str, contenido: str, intencion_id: str | None = None) -> dict:
    """Bitácora de interacciones: la memoria que usa Muuk para adaptar la UI."""
    return db.registrar_interaccion(sesion_id, tipo, contenido, intencion_id)


@mcp.tool
def actualizar_preferencia(user_id: str, intencion_nombre: str, componente_nombre: str, success: bool) -> dict:
    """Actualiza score de preferencia UI por nombre de intención y componente.
    Ej: actualizar_preferencia('u1', 'PAGAR_DEUDA', 'PlanDePago', True)"""
    return db.actualizar_preferencia(user_id, intencion_nombre, componente_nombre, success)

@mcp.tool
def get_retos_disponibles(user_id: str) -> list:
    """Retos activos que el usuario todavía no ha completado."""
    return db.get_retos_disponibles(user_id)

if __name__ == "__main__":
    mcp.run()