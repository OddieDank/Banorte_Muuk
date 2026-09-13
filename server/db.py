"""Capa de datos de Muuk — Tiger Data (PostgreSQL + TimescaleDB).

Esquema real: ver transaccion.sql / schema_additions.sql.
DATABASE_URL configurable por env; default = instancia Timescale Cloud del equipo.
"""

import os
from contextlib import closing
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")  # no pisa vars de entorno ya definidas

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL no está definida. Agrégala a server/.env "
        "(ver server/.env.example)."
    )


def _conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def _clean(v):
    """JSON-safe para tools MCP y FastAPI (psycopg2 devuelve Decimal/datetime/UUID)."""
    if isinstance(v, Decimal):
        return float(v)
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    return v


def _q(sql: str, params: tuple = ()) -> list[dict]:
    with closing(_conn()) as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall() if cur.description else []
        conn.commit()
        return [{k: _clean(v) for k, v in r.items()} for r in rows]


def _q1(sql: str, params: tuple = ()) -> dict | None:
    rows = _q(sql, params)
    return rows[0] if rows else None


# ── Usuario y perfil ──────────────────────────────────────────────────────

def get_usuario(user_id: str) -> dict | None:
    return _q1("SELECT * FROM usuario WHERE user_id = %s", (user_id,))

def validar_login(nombre: str, password: str) -> dict | None:
    """Login real por usuario: nombre (completo o primer nombre) + password.
    Devuelve {user_id, nombre} si las credenciales son válidas, None si no."""
    import hashlib
    h = hashlib.sha256(password.encode()).hexdigest()
    return _q1(
        """SELECT user_id, nombre FROM usuario
           WHERE (lower(nombre) = lower(%s) OR lower(split_part(nombre, ' ', 1)) = lower(%s))
             AND password_hash = %s""",
        (nombre.strip(), nombre.strip(), h),
    )

def get_perfil_financiero(user_id: str) -> dict | None:
    return _q1("SELECT * FROM perfil_financiero WHERE user_id = %s", (user_id,))


def get_presupuesto_estimado(user_id: str) -> list[dict]:
    """Presupuesto implícito por categoría: promedio mensual histórico vs mes
    actual. Semáforo de estado: sobre / al_límite / bajo."""
    return _q(
        """WITH res AS (
               SELECT r.categoria,
                      avg(r.total_gastado) FILTER (WHERE r.mes < date_trunc('month', now())) AS promedio_mensual,
                      max(r.total_gastado) FILTER (WHERE r.mes = date_trunc('month', now())) AS mes_actual
               FROM transaccion_resumen r
               JOIN usuario_producto up ON up.user_product_id = r.user_product_id
               WHERE up.user_id = %s
               GROUP BY r.categoria
           )
           SELECT categoria,
                  round(promedio_mensual, 2) AS promedio_mensual,
                  round(coalesce(mes_actual, 0), 2) AS mes_actual,
                  CASE WHEN mes_actual > promedio_mensual THEN 'sobre'
                       WHEN mes_actual >= promedio_mensual * 0.9 THEN 'al_limite'
                       ELSE 'bajo' END AS estado
           FROM res
           WHERE promedio_mensual IS NOT NULL AND mes_actual IS NOT NULL
           ORDER BY mes_actual DESC""",
        (user_id,),
    )


def get_productos_usuario(user_id: str) -> list[dict]:
    return _q(
        """SELECT up.*, p.nombre, p.tipo, p.descripcion
           FROM usuario_producto up
           JOIN producto p ON p.product_id = up.product_id
           WHERE up.user_id = %s""",
        (user_id,),
    )


def get_resumen_gastos(user_id: str, meses: int = 3) -> list[dict]:
    """Agregados por categoría/mes. ESTO es lo que ve el agente (privacidad:
    nunca la tabla cruda `transaccion`, solo el continuous aggregate)."""
    return _q(
        """SELECT r.mes, r.categoria, r.total_gastado, r.total_ingresos, r.num_movimientos
           FROM transaccion_resumen r
           JOIN usuario_producto up ON up.user_product_id = r.user_product_id
           WHERE up.user_id = %s AND r.mes >= date_trunc('month', now()) - (%s || ' months')::interval
           ORDER BY r.mes DESC, r.total_gastado DESC NULLS LAST""",
        (user_id, meses - 1),
    )


def get_transacciones(user_id: str, limit: int = 20) -> list[dict]:
    """Detalle crudo. SOLO para el endpoint del frontend (rol de aplicación),
    NUNCA se expone como tool MCP del agente."""
    return _q(
        """SELECT t.categoria, t.monto, t.tipo, t.fecha
           FROM transaccion t
           JOIN usuario_producto up ON up.user_product_id = t.user_product_id
           WHERE up.user_id = %s
           ORDER BY t.fecha DESC LIMIT %s""",
        (user_id, limit),
    )


# ── Sesiones e interacciones ──────────────────────────────────────────────

def ensure_sesion(sesion_id: str, user_id: str, canal: str = "web") -> str:
    """Idempotente: /chat y /action la llaman antes de registrar interacciones."""
    _q(
        "INSERT INTO sesion (sesion_id, user_id, canal) VALUES (%s, %s, %s) ON CONFLICT (sesion_id) DO NOTHING",
        (sesion_id, user_id, canal),
    )
    return sesion_id


def registrar_interaccion(sesion_id: str, tipo: str, contenido: str, intencion_id: str | None = None) -> dict:
    return _q1(
        """INSERT INTO interaccion (sesion_id, intencion_id, tipo, contenido)
           VALUES (%s, %s, %s, %s) RETURNING interaccion_id, "timestamp" """,
        (sesion_id, intencion_id, tipo, contenido),
    ) or {}


def get_resumen_interacciones(sesion_id: str, limit: int = 20) -> list[dict]:
    return _q(
        """SELECT tipo, contenido, "timestamp"
           FROM interaccion WHERE sesion_id = %s
           ORDER BY "timestamp" DESC LIMIT %s""",
        (sesion_id, limit),
    )


# ── Resolución nombre → UUID ─────────────────────────────────────────────

def resolve_intencion(nombre: str) -> str | None:
    """'PAGAR_DEUDA' → UUID. None si no existe."""
    row = _q1("SELECT intencion_id FROM intencion WHERE nombre = %s", (nombre,))
    return row["intencion_id"] if row else None


def resolve_componente(nombre: str) -> str | None:
    """'PlanDePago' → UUID. None si no existe."""
    row = _q1("SELECT componente_id FROM componente_ui WHERE nombre = %s", (nombre,))
    return row["componente_id"] if row else None


def seed_componente_ui():
    """Inserta las componentes del catálogo si no existen ya."""
    for nombre, tipo, desc in [
        ("PlanDePago", "financiero", "Opciones de reestructura de deuda con CTA"),
        ("TablaGastos", "financiero", "Tabla de gastos/agregados por categoría"),
        ("Confirmacion", "ui", "Confirmación de acción del usuario"),
        ("GraficaPastel", "visualizacion", "Distribución por categoría (donut, rebanadas clicables)"),
        ("GraficaBarras", "visualizacion", "Serie por periodo (barras clicables)"),
        ("TarjetaMetrica", "resumen", "Métrica destacada con valor grande"),
        ("GraficaLinea", "visualizacion", "Tendencia por periodo (línea, puntos clicables)"),
        ("ProgresoMeta", "meta", "Progreso hacia meta de ahorro (barra con %)"),
    ]:
        if not _q1("SELECT 1 FROM componente_ui WHERE nombre = %s", (nombre,)):
            _q("INSERT INTO componente_ui (nombre, tipo, descripcion) VALUES (%s, %s, %s)", (nombre, tipo, desc))


# ── Preferencias (aprendizaje) ────────────────────────────────────────────

def get_preferencias(user_id: str, intencion_nombre: str | None = None) -> list[dict]:
    """Devuelve preferencias con nombres legibles para el agente."""
    if intencion_nombre:
        intencion_id = resolve_intencion(intencion_nombre)
        if not intencion_id:
            return []
        return _q(
            """SELECT p.*, i.nombre AS intencion_nombre, c.nombre AS componente_nombre
               FROM preferencia_ui p
               JOIN intencion i ON i.intencion_id = p.intencion_id
               JOIN componente_ui c ON c.componente_id = p.componente_id
               WHERE p.user_id = %s AND p.intencion_id = %s""",
            (user_id, intencion_id),
        )
    return _q(
        """SELECT p.*, i.nombre AS intencion_nombre, c.nombre AS componente_nombre
           FROM preferencia_ui p
           JOIN intencion i ON i.intencion_id = p.intencion_id
           JOIN componente_ui c ON c.componente_id = p.componente_id
           WHERE p.user_id = %s
           ORDER BY p.score DESC NULLS LAST""",
        (user_id,),
    )


def actualizar_preferencia(user_id: str, intencion_nombre: str, componente_nombre: str, success: bool):
    """Upsert por nombre de intención y componente. Resuelve UUIDs internamente."""
    intencion_id = resolve_intencion(intencion_nombre)
    componente_id = resolve_componente(componente_nombre)
    if not intencion_id or not componente_id:
        return {"error": f"intención o componente desconocido: {intencion_nombre}/{componente_nombre}"}
    _q(
        """INSERT INTO preferencia_ui (user_id, intencion_id, componente_id, usage_count, success_count, score, ultimo_uso)
           VALUES (%s, %s, %s, 1, %s, %s, now())
           ON CONFLICT (user_id, intencion_id, componente_id)
           DO UPDATE SET
             usage_count = preferencia_ui.usage_count + 1,
             success_count = preferencia_ui.success_count + %s,
             score = (preferencia_ui.success_count + %s)::numeric / (preferencia_ui.usage_count + 1),
             ultimo_uso = now()""",
        (user_id, intencion_id, componente_id, 1 if success else 0, 1 if success else 0, 1 if success else 0, 1 if success else 0),
    )
    return {"ok": True}


# ── Planes de pago ────────────────────────────────────────────────────────

def aplicar_plan(user_id: str, meses: int, pago_mensual: float, cat: float, monto_original: float, interaccion_id: str | None = None, interaccion_ts: str | None = None) -> dict:
    row = _q1(
        """INSERT INTO plan_pago (user_id, interaccion_id, interaccion_ts, meses, pago_mensual, cat, monto_original)
           VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING plan_id""",
        (user_id, interaccion_id, interaccion_ts, meses, pago_mensual, cat, monto_original),
    )
    return {"plan_id": row["plan_id"], "ok": True}


# ── Simulación (pura, sin DB) ─────────────────────────────────────────────

def simular_plan_pago(deuda: float, meses: int, cat: float) -> dict:
    deuda = float(deuda)
    tasa = cat / 100 / 12
    pago = deuda * (tasa * (1 + tasa) ** meses) / ((1 + tasa) ** meses - 1)
    return {"meses": meses, "pago_mensual": round(pago, 2), "cat": cat, "total": round(pago * meses, 2)}


# ── Inicialización ────────────────────────────────────────────────────────

seed_componente_ui()

# ── MUUK Coins ─────────────────────────────────────────────────────────────

def get_muuk_wallet(user_id: str) -> dict | None:
    """Obtiene el saldo actual de Muuk Coins del usuario."""
    return _q1(
        """
        SELECT user_id, muuk_coins, updated_at
        FROM muuk_wallet
        WHERE user_id = %s
        """,
        (user_id,)
    )


def get_muuk_coin_history(user_id: str, limit: int = 20) -> list[dict]:
    """Obtiene el historial de movimientos de Muuk Coins."""
    limit = min(max(limit, 1), 100)

    return _q(
        """
        SELECT
            muuk_coin_transaction_id,
            fecha,
            cantidad,
            tipo,
            descripcion
        FROM muuk_coin_transaction
        WHERE user_id = %s
        ORDER BY fecha DESC
        LIMIT %s
        """,
        (user_id, limit)
    )


def get_retos_disponibles(user_id: str) -> list[dict]:
    """Obtiene retos activos que el usuario aún no ha completado."""
    return _q(
        """
        SELECT
            r.reto_id,
            r.nombre,
            r.descripcion,
            r.recompensa,
            r.condicion_tipo,
            r.condicion_valor,
            r.condicion_categoria
        FROM reto r
        WHERE r.activo = TRUE
          AND NOT EXISTS (
              SELECT 1
              FROM usuario_reto ur
              WHERE ur.user_id = %s
                AND ur.reto_id = r.reto_id
          )
        ORDER BY r.recompensa DESC
        """,
        (user_id,)
    )

# IM SORRY ITS SO LOOONG :(
def validar_y_completar_reto(user_id: str, reto_id: str) -> dict:
    """
    Valida si el usuario cumple el reto.
    Si lo cumple, llama a completar_reto() y otorga las coins.
    """

    reto = _q1(
        """
        SELECT
            reto_id,
            nombre,
            recompensa,
            condicion_tipo,
            condicion_valor,
            condicion_categoria
        FROM reto
        WHERE reto_id = %s
          AND activo = TRUE
        """,
        (reto_id,)
    )

    if not reto:
        return {
            "ok": False,
            "status": "not_found",
            "message": "El reto no existe o está inactivo."
        }

    # ---------------------------------------------------------
    # Evitar completar el mismo reto dos veces
    # ---------------------------------------------------------

    completado = _q1(
        """
        SELECT 1
        FROM usuario_reto
        WHERE user_id = %s
          AND reto_id = %s
        """,
        (user_id, reto_id)
    )

    if completado:
        return {
            "ok": False,
            "status": "already_completed",
            "message": "Este reto ya fue completado."
        }

    cumple = False

    # ---------------------------------------------------------
    # RETO: AHORRO MENSUAL
    # ---------------------------------------------------------

    if reto["condicion_tipo"] == "ahorro_mensual":

        resultado = _q1(
            """
            SELECT
                COALESCE(SUM(total_ingresos), 0)
                -
                COALESCE(SUM(total_gastado), 0)
                AS ahorro
            FROM transaccion_resumen r
            JOIN usuario_producto up
                ON up.user_product_id = r.user_product_id
            WHERE up.user_id = %s
              AND r.mes = date_trunc('month', now())
            """,
            (user_id,)
        )

        ahorro = float(resultado["ahorro"] or 0)

        cumple = ahorro >= float(reto["condicion_valor"])

    # ---------------------------------------------------------
    # RETO: REDUCCIÓN DE CATEGORÍA
    # ---------------------------------------------------------

    elif reto["condicion_tipo"] == "reduccion_categoria":

        resultado = _q1(
            """
            WITH meses AS (
                SELECT
                    r.mes,
                    SUM(r.total_gastado) AS gasto
                FROM transaccion_resumen r
                JOIN usuario_producto up
                    ON up.user_product_id = r.user_product_id
                WHERE up.user_id = %s
                  AND r.categoria = %s
                  AND r.mes >= date_trunc('month', now()) - INTERVAL '1 month'
                GROUP BY r.mes
                ORDER BY r.mes DESC
                LIMIT 2
            )
            SELECT
                MAX(CASE
                    WHEN mes = date_trunc('month', now())
                    THEN gasto
                END) AS actual,

                MAX(CASE
                    WHEN mes = date_trunc('month', now()) - INTERVAL '1 month'
                    THEN gasto
                END) AS anterior
            FROM meses
            """,
            (
                user_id,
                reto["condicion_categoria"]
            )
        )

        actual = float(resultado["actual"] or 0)
        anterior = float(resultado["anterior"] or 0)

        if anterior > 0:
            reduccion = ((anterior - actual) / anterior) * 100
            cumple = reduccion >= float(reto["condicion_valor"])

    # ---------------------------------------------------------
    # SI CUMPLE → otorgar coins
    # ---------------------------------------------------------

    if cumple:

        recompensa = _q1(
            """
            SELECT completar_reto(%s, %s) AS recompensa
            """,
            (user_id, reto_id)
        )

        coins = recompensa["recompensa"]

        wallet = get_muuk_wallet(user_id)

        return {
            "ok": True,
            "status": "completed",
            "reto_id": reto_id,
            "reto": reto["nombre"],
            "coins_earned": coins,
            "balance": wallet["muuk_coins"] if wallet else 0,
            "message": f"¡Reto completado! Ganaste {coins} Muuk Coins."
        }

    return {
        "ok": True,
        "status": "not_completed",
        "reto_id": reto_id,
        "reto": reto["nombre"],
        "coins_earned": 0,
        "message": "Todavía no cumples la condición de este reto."
    }