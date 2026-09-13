import { useState } from "react";
import "./Home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Hero from "../../components/Hero/Hero";
import Header from "../../components/Header/Header";
import SearchBar from "../../components/SearchBar/SearchBar";
import ActionCard from "../../components/ActionCard/ActionCard";
import MuukChat from "../../muuk/MuukChat";
import Perfil from "../Perfil/Perfil";

function Home({ onLogout }) {

    const username = localStorage.getItem("username") || "Usuario";
    const [consulta, setConsulta] = useState("");
    const [vista, setVista] = useState("home");
    const [vozActiva, setVozActiva] = useState(false);

    return (
        <div className="home">

            <Sidebar
                onLogout={onLogout}
                onProfileClick={() => setVista(vista === "perfil" ? "home" : "perfil")}
            />

            <main className="home-content">

                {vista === "perfil" ? (
                    <Perfil onBack={() => setVista("home")} />
                ) : (
                    <>
                        <Hero />

                        <Header
                            username={username}
                            vozActiva={vozActiva}
                            onToggleVoz={() => setVozActiva((v) => !v)}
                        />

                        <SearchBar onSearch={setConsulta} />

                        <MuukChat consulta={consulta} vozActiva={vozActiva} />

                        <section className="quick-actions">

                            <ActionCard
                                title="Regresar al portal Banorte"
                                description="Volver al sitio principal para continuar con tus operaciones bancarias."
                                onClick={() => {
                                    window.location.href = "https://www.banorte.com/";
                                }}
                            />

                        </section>

                    </>
                )}

            </main>

        </div>
    );
}

export default Home;