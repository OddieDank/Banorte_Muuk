import { useState } from "react";
import "./Home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Hero from "../../components/Hero/Hero";
import Header from "../../components/Header/Header";
import SearchBar from "../../components/SearchBar/SearchBar";
import ActionCard from "../../components/ActionCard/ActionCard";
import MuukChat from "../../muuk/MuukChat";

import { describirUI } from "../../services/tts";

function Home({ onLogout }) {

    const username = localStorage.getItem("username") || "Usuario";
    const [consulta, setConsulta] = useState("");

    return (
        <div className="home">

            <Sidebar onLogout={onLogout} />

            <main className="home-content">

                <Hero />

                <Header username={username} />

                <SearchBar onSearch={setConsulta} />

                <MuukChat consulta={consulta} />

                <section className="quick-actions">

                    <ActionCard
                        title="Regresar al portal Banorte"
                        description="Volver al sitio principal para continuar con tus operaciones bancarias."
                        onClick={() => {
                            window.location.href = "https://www.banorte.com/";
                        }}
                    />

                </section>

                <button
                    className="tts-button"
                    onClick={() =>
                        describirUI(
                            "Bienvenido al asistente digital de Banorte."
                        )
                    }
                >
                    Escuchar presentación
                </button>

            </main>

        </div>
    );
}

export default Home;