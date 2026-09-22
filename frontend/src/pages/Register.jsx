import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ShieldCheck, UserPlus } from "lucide-react";

import { register } from "../services/api";

function Register() {
    const navigate = useNavigate();

    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        confirmPassword: ""
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const handleChange = (event) => {
        const { name, value } = event.target;

        setFormData((previous) => ({
            ...previous,
            [name]: value
        }));
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        setError("");
        setSuccess("");

        if (!formData.username.trim()) {
            setError("Username is required.");
            return;
        }

        if (!formData.email.trim()) {
            setError("Email is required.");
            return;
        }

        if (formData.password.length < 8) {
            setError("Password must contain at least 8 characters.");
            return;
        }

        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match.");
            return;
        }

        try {
            setLoading(true);

            await register(
                formData.username.trim(),
                formData.email.trim(),
                formData.password
            );

            setSuccess(
                "Registration successful. Redirecting to login..."
            );

            setTimeout(() => {
                navigate("/login", { replace: true });
            }, 1000);

        } catch (err) {
            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Unable to create your account."
            );
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-page">

            <div className="auth-card">

                <div className="auth-brand">

                    <div className="auth-logo">
                        <ShieldCheck size={28} />
                    </div>

                    <div>
                        <h1>AI Support</h1>
                        <span>Ticket Intelligence</span>
                    </div>

                </div>


                <div className="auth-header">

                    <UserPlus size={22} />

                    <div>
                        <h2>Create Account</h2>
                        <p>
                            Register to access the support intelligence platform.
                        </p>
                    </div>

                </div>


                {error && (
                    <div className="auth-error">
                        {error}
                    </div>
                )}


                {success && (
                    <div className="auth-success">
                        {success}
                    </div>
                )}


                <form
                    className="auth-form"
                    onSubmit={handleSubmit}
                >

                    <div className="form-group">

                        <label htmlFor="username">
                            Username
                        </label>

                        <input
                            id="username"
                            name="username"
                            type="text"
                            value={formData.username}
                            onChange={handleChange}
                            placeholder="Enter username"
                            autoComplete="username"
                            disabled={loading}
                        />

                    </div>


                    <div className="form-group">

                        <label htmlFor="email">
                            Email
                        </label>

                        <input
                            id="email"
                            name="email"
                            type="email"
                            value={formData.email}
                            onChange={handleChange}
                            placeholder="Enter email"
                            autoComplete="email"
                            disabled={loading}
                        />

                    </div>


                    <div className="form-group">

                        <label htmlFor="password">
                            Password
                        </label>

                        <input
                            id="password"
                            name="password"
                            type="password"
                            value={formData.password}
                            onChange={handleChange}
                            placeholder="Minimum 8 characters"
                            autoComplete="new-password"
                            disabled={loading}
                        />

                    </div>


                    <div className="form-group">

                        <label htmlFor="confirmPassword">
                            Confirm Password
                        </label>

                        <input
                            id="confirmPassword"
                            name="confirmPassword"
                            type="password"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            placeholder="Confirm password"
                            autoComplete="new-password"
                            disabled={loading}
                        />

                    </div>


                    <button
                        type="submit"
                        className="primary-button auth-submit"
                        disabled={loading}
                    >
                        {loading
                            ? "Creating Account..."
                            : "Create Account"}
                    </button>

                </form>


                <div className="auth-footer">

                    <span>
                        Already have an account?
                    </span>

                    <Link to="/login">
                        Sign in
                    </Link>

                </div>


                <div className="auth-role-note">
                    New accounts are created with Viewer access.
                </div>

            </div>

        </div>
    );
}

export default Register;