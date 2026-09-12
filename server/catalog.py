"""Catálogo A2UI propio de Muuk (subset v0.9.1).

Los únicos componentes que el agente puede renderizar viven aquí.
El servidor valida cada salida del LLM contra este catálogo antes de SSE;
componente desconocido → fallo cerrado (anti UI-injection).
"""

from typing import Optional

from pydantic import BaseModel, Field


# ── Componentes del catálogo ──────────────────────────────────────────────

class OpcionPago(BaseModel):
    meses: int = Field(gt=0, le=360)
    pago_mensual: float = Field(gt=0)
    cat: float = Field(gt=0, le=1000)

class PlanDePago(BaseModel):
    mensaje: str
    opciones: list[OpcionPago]
    cta: str = "Aplicar plan"

class FilaGasto(BaseModel):
    concepto: str
    monto: float
    categoria: str

class TablaGastos(BaseModel):
    titulo: str
    # Dos modos: filas literales (agregados) o dataRef (el frontend trae el
    # detalle directo del API; el LLM nunca ve transacciones crudas).
    filas: Optional[list[FilaGasto]] = None
    dataRef: Optional[str] = None

class Confirmacion(BaseModel):
    mensaje: str
    detalles: Optional[dict] = None

# Catálogo: type → schema de props. Cualquier otro type se rechaza.
CATALOG: dict[str, type[BaseModel]] = {
    "PlanDePago": PlanDePago,
    "TablaGastos": TablaGastos,
    "Confirmacion": Confirmacion,
}


def validar_componente(componentType: str, props: dict) -> bool:
    """Franja de seguridad: el agente solo puede usar tipos del catálogo."""
    schema = CATALOG.get(componentType)
    if schema is None:
        return False
    try:
        schema.model_validate(props)
        return True
    except Exception:
        return False


def new_message(bucket: str, **payload) -> dict:
    """Envoltura simple para SSE; el adapter del frontend para un único mensaje."""
    return {"type": bucket, **payload}
