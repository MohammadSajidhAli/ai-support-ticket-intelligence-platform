import {
    BrowserRouter,
    Routes,
    Route,
    Navigate
} from "react-router-dom";

import Dashboard from "./pages/Dashboard";
import TicketDetails from "./pages/TicketDetails";
import Login from "./pages/Login";
import Register from "./pages/Register";


function ProtectedRoute({ children }) {

    const token =
        localStorage.getItem("access_token");

    if (!token) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }

    return children;
}


function App() {

    return (

        <BrowserRouter>

            <Routes>

                {/* PUBLIC ROUTES */}

                <Route
                    path="/login"
                    element={<Login />}
                />

                <Route
                    path="/register"
                    element={<Register />}
                />


                {/* PROTECTED ROUTES */}

                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />

                <Route
                    path="/tickets/:ticketId"
                    element={
                        <ProtectedRoute>
                            <TicketDetails />
                        </ProtectedRoute>
                    }
                />


                {/* FALLBACK */}

                <Route
                    path="*"
                    element={
                        <Navigate
                            to="/"
                            replace
                        />
                    }
                />

            </Routes>

        </BrowserRouter>
    );
}


export default App;