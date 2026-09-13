"""Catálogo A2UI propio de Muuk (subset v0.9.1).

Los únicos componentes que el agente puede renderizar viven aquí.
El servidor valida cada salida del LLM contra este catálogo antes de SSE;
componente desconocido → fallo cerrado (anti UI-injection).

"info" (prop opcional, heredada de InfoMixin): frase explicativa que el
frontend muestra como tarjeta al poner el cursor encima del componente.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ── Propiedad común: tarjeta de info al cursor ───────────────────────────

class InfoMixin(BaseModel):
    info: Optional[str] = None


# ── Componentes del catálogo ──────────────────────────────────────────────

class OpcionPago(BaseModel):
    meses: int = Field(gt=0, le=360)
    pago_mensual: float = Field(gt=0)
    cat: float = Field(gt=0, le=1000)
    total: Optional[float] = None

class PlanDePago(InfoMixin):
    mensaje: str
    monto_original: float = Field(gt=0)
    opciones: list[OpcionPago]
    cta: str = "Aplicar plan"

class FilaGasto(BaseModel):
    concepto: str
    monto: float
    categoria: str

class TablaGastos(InfoMixin):
    titulo: str
    # Dos modos: filas literales (agregados) o dataRef (el frontend trae el
    # detalle directo del API; el LLM nunca ve transacciones crudas).
    filas: Optional[list[FilaGasto]] = None
    dataRef: Optional[str] = None

class Confirmacion(BaseModel):
    mensaje: str
    detalles: Optional[dict] = None

class Segmento(BaseModel):
    etiqueta: str
    valor: float = Field(gt=0)

class GraficaPastel(InfoMixin):
    titulo: str
    segmentos: list[Segmento]

class Barra(BaseModel):
    etiqueta: str
    valor: float = Field(gt=0)

class GraficaBarras(InfoMixin):
    titulo: str
    barras: list[Barra]

class Punto(BaseModel):
    etiqueta: str
    valor: float = Field(gt=0)

class GraficaLinea(InfoMixin):
    titulo: str
    puntos: list[Punto]

class TarjetaMetrica(InfoMixin):
    titulo: str
    valor: str  # ya formateado: "$8,500" o "+18.4%"
    subtitulo: Optional[str] = None

class ProgresoMeta(InfoMixin):
    titulo: str
    actual: float = Field(ge=0)
    meta: float = Field(gt=0)

class RetoFinanciero(InfoMixin):
    reto_id: str
    titulo: str
    descripcion: str
    recompensa: int
    cta: str = "Aceptar reto"

class ComandoUI(BaseModel):
    """Comandos de interfaz: el frontend los ejecuta localmente (modo oscuro,
    exportar PDF). El dispatch igual se registra para aprendizaje."""
    accion: Literal["modo_oscuro", "exportar_pdf"]
    label: Optional[str] = None

# Catálogo: type → schema de props. Cualquier otro type se rechaza.
CATALOG: dict[str, type[BaseModel]] = {
    "PlanDePago": PlanDePago,
    "TablaGastos": TablaGastos,
    "Confirmacion": Confirmacion,
    "GraficaPastel": GraficaPastel,
    "GraficaBarras": GraficaBarras,
    "GraficaLinea": GraficaLinea,
    "TarjetaMetrica": TarjetaMetrica,
    "ProgresoMeta": ProgresoMeta,
    "ComandoUI": ComandoUI,
    "RetoFinanciero": RetoFinanciero,
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

