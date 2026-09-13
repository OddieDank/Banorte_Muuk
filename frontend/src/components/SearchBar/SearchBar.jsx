import { useRef, useState } from "react";
import "./SearchBar.css";

const API = "http://localhost:8000";

// Umbral de volumen para considerar que hay voz (0 a 1, escala RMS).
const UMBRAL_VOZ = 0.02;
// Silencio sostenido antes de cortar la grabación sola.
const SILENCIO_MS = 1200;
// Tope de seguridad por si la detección de silencio nunca dispara.
const MAX_GRABACION_MS = 15000;

function SearchBar({ onSearch }) {
    const [query, setQuery] = useState("");
    const [escuchando, setEscuchando] = useState(false);
    const [procesando, setProcesando] = useState(false);

    const streamRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const audioContextRef = useRef(null);
    const analyserRef = useRef(null);
    const rafRef = useRef(null);
    const maxTimeoutRef = useRef(null);
    const habloRef = useRef(false);
    const ultimoSonidoRef = useRef(0);

    const handleSearch = (textoOverride) => {
        const texto = (textoOverride ?? query).trim();
        if (!texto) return;

        if (onSearch) {
            onSearch(texto);
        }
        setQuery(""); // limpia la barra al enviar
    };

    const handleKeyDown = (event) => {
        if (event.key === "Enter") {
            handleSearch();
        }
    };

    const limpiarRecursos = () => {
        if (rafRef.current) cancelAnimationFrame(rafRef.current);
        if (maxTimeoutRef.current) clearTimeout(maxTimeoutRef.current);
        if (audioContextRef.current) audioContextRef.current.close();
        if (streamRef.current) {
            streamRef.current.getTracks().forEach((t) => t.stop());
        }
        streamRef.current = null;
        audioContextRef.current = null;
        analyserRef.current = null;
        rafRef.current = null;
        maxTimeoutRef.current = null;
    };

    const monitorearVolumen = () => {
        const analyser = analyserRef.current;
        if (!analyser) return;

        const datos = new Uint8Array(analyser.fftSize);
        analyser.getByteTimeDomainData(datos);

        let suma = 0;
        for (let i = 0; i < datos.length; i++) {
            const v = (datos[i] - 128) / 128;
            suma += v * v;
        }
        const rms = Math.sqrt(suma / datos.length);
        console.log("volumen:", rms.toFixed(4));  // TEMPORAL, quitar después

        if (rms > UMBRAL_VOZ) {
            habloRef.current = true;
            ultimoSonidoRef.current = Date.now();
        }

        const silencioLargo =
            habloRef.current && Date.now() - ultimoSonidoRef.current > SILENCIO_MS;

        if (silencioLargo) {
            detenerGrabacion();
            return;
        }

        rafRef.current = requestAnimationFrame(monitorearVolumen);
    };

    const detenerGrabacion = () => {
        if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
            mediaRecorderRef.current.stop();
        }
        setEscuchando(false);
    };

    const handleVoice = async () => {
        if (escuchando) {
            detenerGrabacion();
            return;
        }

        if (!navigator.mediaDevices?.getUserMedia) {
            alert("Tu navegador no soporta grabación de audio.");
            return;
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const audioContext = new AudioContext();
            await audioContext.resume();
            const source = audioContext.createMediaStreamSource(stream);
            const analyser = audioContext.createAnalyser();
            analyser.fftSize = 2048;
            source.connect(analyser);

            audioContextRef.current = audioContext;
            analyserRef.current = analyser;
            habloRef.current = false;
            ultimoSonidoRef.current = Date.now();
            chunksRef.current = [];

            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) chunksRef.current.push(event.data);
            };

            mediaRecorder.onstop = async () => {
                limpiarRecursos();

                const audioBlob = new Blob(chunksRef.current, { type: "audio/webm" });
                chunksRef.current = [];

                if (audioBlob.size === 0) return;

                setProcesando(true);
                try {
                    const formData = new FormData();
                    formData.append("file", audioBlob, "grabacion.webm");

                    const respuesta = await fetch(`${API}/stt`, {
                        method: "POST",
                        body: formData,
                    });

                    if (!respuesta.ok) {
                        console.error("Error transcribiendo:", await respuesta.text());
                        return;
                    }

                    const data = await respuesta.json();
                    setQuery(data.text);
                    handleSearch(data.text);
                } catch (err) {
                    console.error("Error al mandar audio a /stt:", err);
                } finally {
                    setProcesando(false);
                }
            };

            mediaRecorder.start();
            setEscuchando(true);

            maxTimeoutRef.current = setTimeout(detenerGrabacion, MAX_GRABACION_MS);
            rafRef.current = requestAnimationFrame(monitorearVolumen);
        } catch (err) {
            console.error("No se pudo acceder al micrófono:", err);
            alert("No se pudo acceder al micrófono. Revisa los permisos del navegador.");
        }
    };

    return (
        <div className="search-bar">

            <button
                className="search-menu-button"
                type="button"
                aria-label="Abrir menú"
            >
                <span className="menu-line"></span>
                <span className="menu-line"></span>
                <span className="menu-line"></span>
            </button>

            <input
                type="text"
                className="search-input"
                placeholder={
                    escuchando
                        ? "Escuchando..."
                        : procesando
                        ? "Transcribiendo..."
                        : "Haz una pregunta"
                }
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onKeyDown={handleKeyDown}
            />

            <button
                className={`search-voice-button${escuchando ? " search-voice-active" : ""}`}
                type="button"
                aria-label="Usar micrófono"
                onClick={handleVoice}
                disabled={procesando}
            >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                >
                    <rect
                        x="9"
                        y="3"
                        width="6"
                        height="11"
                        rx="3"
                    />
                    <path d="M5 11a7 7 0 0 0 14 0" />
                    <path d="M12 18v3" />
                    <path d="M8 21h8" />
                </svg>
            </button>

            <button
                className="search-submit-button"
                type="button"
                onClick={() => handleSearch()}
                aria-label="Buscar"
            >
                <svg
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                >
                    <circle cx="11" cy="11" r="7" />
                    <path d="m20 20-4-4" />
                </svg>
            </button>

        </div>
    );
}

export default SearchBar;