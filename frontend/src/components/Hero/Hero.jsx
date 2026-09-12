import logo from "../../public/banorte-logo.svg";
import heroImage from "../../public/img2.jpg";
import "./Hero.css";

function Hero() {
    return (
        <section className="hero">

            <div
                className="hero-background"
                style={{ backgroundImage: `url(${heroImage})` }}
            ></div>

            <div className="hero-content">

                <div className="hero-logo-container">
                    <img
                        src={logo}
                        alt="Banorte"
                        className="hero-logo"
                    />
                </div>

                <div className="hero-line"></div>

                <p className="hero-subtitle">
                    Asistente digital
                </p>

            </div>

        </section>
    );
}

export default Hero;