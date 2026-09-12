// MuukChat — conecta la app con el agente: POST /chat (SSE) → adapter A2UI
// → registry → componentes. dispatch de acciones → POST /action (loop cerrado).
import { useEffect, useRef, useState } from "react";
import { applyMessage } from "../a2ui/adapter";
import { renderComponent } from "../a2ui/registry";
import "../components/PlanDePago";
import "../components/TablaGastos";
import "../components/Confirmacion";
import "../components/PlanDePago.css";
import "./MuukChat.css";

const API = "http://localhost:8000";
const SESSION_ID = crypto.randomUUID();

function MuukChat({ consulta }) {
    const [bloques, setBloques] = useState([]);
    const surfacesRef = useRef({});

    useEffect(() => {
        if (!consulta) return;
        const ctrl = new AbortController();

        (async () => {
            setBloques((b) => [...b, { tipo: "user", texto: consulta }]);
            const res = await fetch(`${API}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: SESSION_ID, mensaje: consulta }),
                signal: ctrl.signal,
            });

            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buf = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                buf += decoder.decode(value, { stream: true });
                const partes = buf.split("\n\n");
                buf = partes.pop();

                for (const p of partes) {
                    const linea = p.trim();
                    if (!linea.startsWith("data:")) continue;
                    const msg = JSON.parse(linea.slice(5));

                    if (msg.type === "dataModelUpdate" && msg.path === "/meta") {
                        setBloques((b) => [...b, { tipo: "texto", texto: msg.value.texto }]);
                    } else {
                        surfacesRef.current = applyMessage(surfacesRef.current, msg);
                        if (msg.type === "surfaceUpdate") {
                            const surface = surfacesRef.current[msg.surfaceId];
                            setBloques((b) => [...b, { tipo: "surface", id: msg.surfaceId, surface }]);
                        }
                    }
                }
            }
        })().catch((e) => {
            if (e.name !== "AbortError") {
                setBloques((b) => [...b, { tipo: "texto", texto: `Error: ${e.message}` }]);
            }
        });

        return () => ctrl.abort();
    }, [consulta]);

    const dispatch = async (accion) => {
        const res = await fetch(`${API}/action`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...accion, session_id: SESSION_ID }),
        });
        const data = await res.json();
        setBloques((b) => [...b, {
            tipo: "texto",
            texto: data.plan ? `Plan aplicado (id ${data.plan.plan_id}).` : "Acción registrada.",
        }]);
    };

    if (bloques.length === 0) return null;

    return (
        <section className="muuk-chat">
            {bloques.map((b, i) =>
                b.tipo === "surface" ? (
                    <div key={i}>
                        {b.surface.components.map((c) => (
                            <div key={c.componentId}>{renderComponent(c, dispatch)}</div>
                        ))}
                    </div>
                ) : (
                    <p key={i} className={b.tipo === "user" ? "muuk-user" : "muuk-texto"}>{b.texto}</p>
                )
            )}
        </section>
    );
}

export default MuukChat;
