
import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

import {
    ShieldCheck,
    LogIn,
    AlertCircle
} from "lucide-react";

import { login } from "../services/api";


function Login() {

    const navigate = useNavigate();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    // ============================================================
    // LOGIN
    // ============================================================

    const handleLogin = async (event) => {

        event.preventDefault();

        if (loading) return;

        try {

            setLoading(true);
            setError("");

            const data = await login(
                username,
                password
            );


            // ----------------------------------------------------
            // STORE AUTHENTICATION TOKEN
            // ----------------------------------------------------

            localStorage.setItem(
                "access_token",
                data.access_token
            );


            // ----------------------------------------------------
            // STORE USER INFORMATION
            // ----------------------------------------------------

            if (data.user) {

                localStorage.setItem(
                    "username",
                    data.user.username
                );

                localStorage.setItem(
                    "role",
                    data.user.role
                );
            }


            // ----------------------------------------------------
            // REDIRECT TO DASHBOARD
            // ----------------------------------------------------

            navigate("/", {
                replace: true
            });

        } catch (err) {

            console.error(
                "Login error:",
                err
            );

            setError(
                err.response?.data?.detail ||
                "Invalid username or password."
            );

        } finally {

            setLoading(false);

        }
    };


    // ============================================================
    // RENDER
    // ============================================================

    return (

        <div className="login-page">

            <div className="login-card">


                {/* ==================================================
                    BRAND
                ================================================== */}

                <div className="login-brand">

                    <div className="login-icon">

                        <ShieldCheck size={27} />

                    </div>

                    <div>

                        <h1>
                            AI Support Platform
                        </h1>

                        <p>
                            AI-powered incident investigation
                        </p>

                    </div>

                </div>


                {/* ==================================================
                    HEADER
                ================================================== */}

                <div className="login-heading">

                    <h2>
                        Welcome back
                    </h2>

                    <p>
                        Sign in to access your support dashboard.
                    </p>

                </div>


                {/* ==================================================
                    ERROR
                ================================================== */}

                {error && (

                    <div className="login-error">

                        <AlertCircle size={18} />

                        <span>
                            {error}
                        </span>

                    </div>

                )}


                {/* ==================================================
                    LOGIN FORM
                ================================================== */}

                <form
                    onSubmit={handleLogin}
                    className="login-form"
                >


                    {/* USERNAME */}

                    <div className="form-group">

                        <label htmlFor="username">
                            Username
                        </label>

                        <input
                            id="username"
                            type="text"
                            value={username}
                            onChange={(event) =>
                                setUsername(
                                    event.target.value
                                )
                            }
                            placeholder="Enter your username"
                            autoComplete="username"
                            disabled={loading}
                            required
                        />

                    </div>


                    {/* PASSWORD */}

                    <div className="form-group">

                        <label htmlFor="password">
                            Password
                        </label>

                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(event) =>
                                setPassword(
                                    event.target.value
                                )
                            }
                            placeholder="Enter your password"
                            autoComplete="current-password"
                            disabled={loading}
                            required
                        />

                    </div>


                    {/* LOGIN BUTTON */}

                    <button
                        type="submit"
                        disabled={loading}
                        className="login-button"
                    >

                        {loading ? (

                            <>
                                <div
                                    style={{
                                        width: "18px",
                                        height: "18px",
                                        border: "2px solid rgba(255,255,255,0.35)",
                                        borderTopColor: "#ffffff",
                                        borderRadius: "50%",
                                        animation: "spin 0.8s linear infinite"
                                    }}
                                />

                                Signing in...
                            </>

                        ) : (

                            <>
                                <LogIn size={18} />

                                Sign In
                            </>

                        )}

                    </button>


                    {/* REGISTER */}

                    <div className="auth-footer">

                        <span>
                            Don't have an account?
                        </span>

                        <Link to="/register">
                            Create Account
                        </Link>

                    </div>

                </form>


                {/* ==================================================
                    FOOTER
                ================================================== */}

                <p
                    style={{
                        textAlign: "center",
                        fontSize: "11px",
                        color: "#94a3b8",
                        marginTop: "22px",
                        marginBottom: 0
                    }}
                >
                    Secure access • AI Incident Investigation Platform
                </p>

            </div>

        </div>
    );
}


export default Login;
