// MuukChat — conecta la app con el agente: POST /chat (SSE) → adapter A2UI
// → registry → componentes. dispatch de acciones → POST /action (loop cerrado).
import { useEffect, useRef, useState } from "react";
import { applyMessage } from "../a2ui/adapter";
import { renderComponent } from "../a2ui/registry";
import "../components/PlanDePago";
import "../components/TablaGastos";
import "../components/Confirmacion";
import "../components/GraficaPastel";
import "../components/GraficaBarras";
import "../components/GraficaLinea";
import "../components/ProgresoMeta";
import "../components/ComandoUI";
import "../components/TarjetaMetrica";
import "../components/PlanDePago.css";
import "../components/Graficas.css";
import "./MuukChat.css";
import { describirUI } from "../services/tts";

const API = "http://localhost:8000";
// user_id se lee en cada fetch: cachearlo en el módulo congela al primer
// usuario logueado (bug: inicias con Marisol y ves datos de Ana).
const getUserId = () => localStorage.getItem("user_id");

function MuukChat({ consulta }) {
    const [bloques, setBloques] = useState([]);
    const [cargando, setCargando] = useState(false);
    const [perfil, setPerfil] = useState("estandar");
    const [vozActiva, setVozActiva] = useState(false);
    const surfacesRef = useRef({});
    const sessionRef = useRef(crypto.randomUUID());

    useEffect(() => {
        if (!consulta) return;
        const ctrl = new AbortController();

        setCargando(true);

        (async () => {
            setBloques((b) => [...b, { tipo: "user", texto: consulta }]);
            const res = await fetch(`${API}/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionRef.current, mensaje: consulta, user_id: getUserId() }),
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

                    if (msg.type === "dataModelUpdate" && msg.path === "/perfil") {
                        // Perfil UI del usuario (edad): senior → letra grande.
                        setPerfil(msg.value?.perfil === "senior" ? "senior" : "estandar");
                    } else if (msg.type === "dataModelUpdate" && msg.path === "/meta") {
                        setBloques((b) => [...b, { tipo: "texto", texto: msg.value.texto }]);
                        if (vozActiva) describirUI(msg.value.texto);
                    } else {
                        surfacesRef.current = applyMessage(surfacesRef.current, msg);
                        if (msg.type === "surfaceUpdate") {
                            const surface = surfacesRef.current[msg.surfaceId];
                            setBloques((b) => [...b, { tipo: "surface", id: msg.surfaceId, surface }]);
                        }
                    }
                }
            }
            setCargando(false);
        })().catch((e) => {
            if (e.name !== "AbortError") {
                setBloques((b) => [...b, { tipo: "texto", texto: `Error: ${e.message}` }]);
            }
            setCargando(false);
        });

        return () => ctrl.abort();
    }, [consulta]);

    const dispatch = async (accion) => {
        const res = await fetch(`${API}/action`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...accion, session_id: sessionRef.current, user_id: getUserId() }),
        });
        const data = await res.json();
        if (data.plan) {
            setBloques((b) => [...b, {
                tipo: "texto",
                texto: `Plan aplicado (id ${data.plan.plan_id}).`,
            }]);
        }
    };

    if (bloques.length === 0 && !cargando) return null;

    return (
        <section className={`muuk-chat ${perfil === "senior" ? "muuk-perfil-senior" : ""}`}>
            <button
                type="button"
                className="voz-toggle"
                onClick={() => setVozActiva((v) => !v)}
            >
                {vozActiva ? "🔊 Voz activada" : "🔇 Voz desactivada"}
            </button>
            {bloques.map((b, i) =>
                b.tipo === "surface" ? (
                    <div key={i} className="muuk-surface">
                        {b.surface.components.map((c) => (
                            <div key={c.componentId} className={c.componentType?.startsWith("Grafica") ? "muuk-grande" : ""}>{renderComponent(c, dispatch)}</div>
                        ))}
                    </div>
                ) : (
                    <p key={i} className={b.tipo === "user" ? "muuk-user" : "muuk-texto"}>{b.texto}</p>
                )
            )}
            {cargando && (
                <div className="muuk-loader">
                    <span className="muuk-loader-texto">Muuk está generando tu interfaz</span>
                    <span className="muuk-loader-dot" />
                    <span className="muuk-loader-dot" />
                    <span className="muuk-loader-dot" />
                </div>
            )}
        </section>
    );
}

export default MuukChat;
