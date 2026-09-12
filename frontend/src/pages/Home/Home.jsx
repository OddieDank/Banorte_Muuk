import "./Home.css";

import Sidebar from "../../components/Sidebar/Sidebar";
import Hero from "../../components/Hero/Hero";
import Header from "../../components/Header/Header";
import SearchBar from "../../components/SearchBar/SearchBar";
import ActionCard from "../../components/ActionCard/ActionCard";

function Home({ onLogout }) {

    const username = localStorage.getItem("username") || "Usuario";

    return (
        <div className="home">

            <Sidebar onLogout={onLogout} />

            <main className="home-content">

                <Hero />

                <Header username={username} />

                <SearchBar
                    onSearch={(query) => {
                        console.log("Pregunta:", query);
                    }}
                />

                <section className="quick-actions">

                    <ActionCard
                        title="Regresar al portal Banorte"
                        description="Volver al sitio principal para continuar con tus operaciones bancarias."
                        onClick={() => {
                            window.location.href = "https://www.banorte.com/";
                        }}
                    />

                    <ActionCard
                        title="Asistente financiero"
                        description="Consulta información sobre productos, movimientos y servicios disponibles."
                    />

                </section>

            </main>

        </div>
    );
}

export default Home;