import { useState } from "react";
import Login from "./pages/Login/Login";
import Home from "./pages/Home/Home";
import "./App.css";

function App() {

    const [isAuthenticated, setIsAuthenticated] = useState(
        Boolean(localStorage.getItem("user_id"))
    );

    const handleLogin = () => {
        // Login.jsx ya guardó user_id y username en localStorage
        setIsAuthenticated(true);
    };

    const handleLogout = () => {
        localStorage.removeItem("user_id");
        localStorage.removeItem("username");
        setIsAuthenticated(false);
    };

    if (!isAuthenticated) {
        return <Login onLogin={handleLogin} />;
    }

    return <Home onLogout={handleLogout} />;
}

export default App;