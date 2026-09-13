"""Muuk → AG-UI: envelope A2UI v0.9 oficial sobre eventos AG-UI.

El agente emite componentes ya validados (catalog.py, fail-closed); este
módulo los convierte a ops oficiales (createSurface / updateComponents /
updateDataModel) y los envuelve en ACTIVITY_SNAPSHOT con
activityType="a2ui-surface" — exactamente lo que hace @ag-ui/a2ui-middleware
al traducir `a2ui_operations` al wire AG-UI.

El frontend lo consume con @copilotkit/a2ui-renderer (useA2UI().processMessages).
"""

import uuid

from ag_ui.core.events import (
    ActivitySnapshotEvent,
    CustomEvent,
    RunStartedEvent,
    RunFinishedEvent,
    TextMessageStartEvent,
    TextMessageContentEvent,
    TextMessageEndEvent,
)
from ag_ui_a2ui_toolkit import create_surface, update_components

# El mismo id se registra en frontend/src/lib/a2ui/muukCatalog.jsx.
CATALOG_ID = "muuk-catalog"
A2UI_ACTIVITY_TYPE = "a2ui-surface"
A2UI_OPERATIONS_KEY = "a2ui_operations"


def componentes_a_ops(componentes: list, surface_id: str) -> list[dict]:
    """Componentes validados → ops A2UI v0.9. Siempre con root para el renderer."""
    ids = []
    nodes = []
    for i, c in enumerate(componentes):
        cid = f"c{i}"
        ids.append(cid)
        nodes.append({"id": cid, "component": c.type, **c.props})
    root = {"id": "root", "component": "Column", "children": ids}
    return [
        create_surface(surface_id, CATALOG_ID),
        update_components(surface_id, [root, *nodes]),
    ]


def run_events(session_id: str, agente, perfil: dict) -> list:
    """Respuesta del agente → lista de eventos AG-UI listos para EventEncoder."""
    thread_id = session_id
    run_id = uuid.uuid4().hex
    events = [RunStartedEvent(thread_id=thread_id, run_id=run_id)]

    # Prosa del agente: mensaje de texto AG-UI estándar.
    if agente.texto:
        msg_id = uuid.uuid4().hex
        events.append(TextMessageStartEvent(role="assistant", message_id=msg_id))
        events.append(TextMessageContentEvent(message_id=msg_id, delta=agente.texto))
        events.append(TextMessageEndEvent(message_id=msg_id))

    # Superficie A2UI: una sola snapshot con todas las ops (orden aplica create→update).
    ops = componentes_a_ops(agente.componentes, f"s-{session_id}-{uuid.uuid4().hex[:6]}")
    if ops:
        events.append(ActivitySnapshotEvent(
            message_id=f"a2ui-surface-{run_id}",
            activity_type=A2UI_ACTIVITY_TYPE,
            content={A2UI_OPERATIONS_KEY: ops},
            replace=True,
        ))

    # Perfil UI (senior/estándar): evento custom; el frontend aplica la clase CSS.
    events.append(CustomEvent(name="muuk-perfil", value=perfil))
    events.append(RunFinishedEvent(thread_id=thread_id, run_id=run_id))
    return events


def error_events(session_id: str, mensaje: str) -> list:
    thread_id = session_id
    run_id = uuid.uuid4().hex
    msg_id = uuid.uuid4().hex
    return [
        RunStartedEvent(thread_id=thread_id, run_id=run_id),
        TextMessageStartEvent(role="assistant", message_id=msg_id),
        TextMessageContentEvent(message_id=msg_id, delta=mensaje),
        TextMessageEndEvent(message_id=msg_id),
        RunFinishedEvent(thread_id=thread_id, run_id=run_id),
    ]
