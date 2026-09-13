// MuukChat — conecta la app con el agente: POST /chat (stream AG-UI) →
// useA2UI().processMessages(ops v0.9) → A2UIRenderer → componentes.
// onAction → POST /action (loop cerrado, igual que antes).
import { useEffect, useRef, useState, useCallback } from "react";
import { A2UIProvider, A2UIRenderer, useA2UI } from "@copilotkit/a2ui-renderer";
import { muukCatalog } from "../lib/a2ui/muukCatalog";
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
    const sessionRef = useRef(crypto.randomUUID());
    const [perfil, setPerfil] = useState("estandar");
    const [vozActiva, setVozActiva] = useState(false);

    const onAction = useCallback(async (accion) => {
        // El payload llega tal cual lo despachó el componente (componente/evento/payload).
        const res = await fetch(`${API}/action`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...accion, session_id: sessionRef.current, user_id: getUserId() }),
        });
        const data = await res.json();
        if (data.plan) {
            // se expone como "flotante" — ChatInner lo agrega como burbuja vía eventBus simple:
            window.dispatchEvent(new CustomEvent("muuk-action-result", { detail: data.plan }));
        }
    }, []);

    return (
        <A2UIProvider catalog={muukCatalog} onAction={onAction}>
            <ChatInner consulta={consulta} perfil={perfil} setPerfil={setPerfil}
                sessionRef={sessionRef} vozActiva={vozActiva} setVozActiva={setVozActiva} />
        </A2UIProvider>
    );
}

function ChatInner({ consulta, perfil, setPerfil, sessionRef, vozActiva, setVozActiva }) {
    const [bloques, setBloques] = useState([]);
    const [cargando, setCargando] = useState(false);
    const a2ui = useA2UI();
    const a2uiRef = useRef(a2ui);
    a2uiRef.current = a2ui;

    useEffect(() => {
        const handler = (e) => {
            const plan = e.detail;
            setBloques((b) => [...b, { tipo: "texto", texto: `Plan aplicado (id ${plan.plan_id}).` }]);
        };
        window.addEventListener("muuk-action-result", handler);
        return () => window.removeEventListener("muuk-action-result", handler);
    }, []);

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
            let textoAcumulado = "";

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

                    if (msg.type === "CUSTOM" && msg.name === "muuk-perfil") {
                        // Perfil UI del usuario (edad): senior → letra grande.
                        setPerfil(msg.value?.perfil === "senior" ? "senior" : "estandar");
                    } else if (msg.type === "TEXT_MESSAGE_CONTENT") {
                        textoAcumulado += msg.delta || "";
                    } else if (msg.type === "TEXT_MESSAGE_END") {
                        if (textoAcumulado) {
                            setBloques((b) => [...b, { tipo: "texto", texto: textoAcumulado }]);
                            if (vozActiva) describirUI(textoAcumulado);
                            textoAcumulado = "";
                        }
                    } else if (msg.type === "ACTIVITY_SNAPSHOT" && msg.activityType === "a2ui-surface") {
                        const ops = msg.content?.a2ui_operations || [];
                        const createOp = ops.find((o) => o.createSurface);
                        const surfaceId = createOp?.createSurface?.surfaceId;
                        a2uiRef.current.processMessages(ops);
                        if (surfaceId) {
                            setBloques((b) => [...b, { tipo: "surface", id: surfaceId }]);
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
                        <A2UIRenderer surfaceId={b.id} />
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
