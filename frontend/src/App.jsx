import { useState } from "react";
import Login from "./pages/Login/Login";
import Home from "./pages/Home/Home";
import "./App.css";

function App() {

    const [isAuthenticated, setIsAuthenticated] = useState(
        Boolean(localStorage.getItem("username"))
    );

    const handleLogin = (username) => {
        localStorage.setItem("username", username);
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        localStorage.removeItem("username");
        setIsAuthenticated(false);
    };

    if (!isAuthenticated) {
        return <Login onLogin={handleLogin} />;
    }

    return <Home onLogout={handleLogout} />;
}

export default App;