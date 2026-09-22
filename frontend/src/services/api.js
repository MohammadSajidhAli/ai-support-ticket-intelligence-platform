import axios from "axios";

const api = axios.create({
    baseURL:
        import.meta.env.VITE_API_URL ||
        "http://127.0.0.1:8000",
    headers: {
        "Content-Type": "application/json"
    }
});


// ============================================================
// REQUEST INTERCEPTOR
// ============================================================

api.interceptors.request.use(
    (config) => {
        const token =
            localStorage.getItem("access_token");

        if (token) {
            config.headers.Authorization =
                `Bearer ${token}`;
        }

        return config;
    },
    (error) => Promise.reject(error)
);


// ============================================================
// RESPONSE INTERCEPTOR
// ============================================================

api.interceptors.response.use(
    (response) => response,
    (error) => {

        if (error.response?.status === 401) {

            localStorage.removeItem(
                "access_token"
            );

            localStorage.removeItem(
                "username"
            );

            localStorage.removeItem(
                "role"
            );

            window.location.href = "/login";
        }

        return Promise.reject(error);
    }
);


// ============================================================
// AUTH
// ============================================================

export const register = async (
    username,
    email,
    password
) => {

    const response = await api.post(
        "/auth/register",
        {
            username,
            email,
            password
        }
    );

    return response.data;
};


export const login = async (
    username,
    password
) => {

    const formData =
        new URLSearchParams();

    formData.append(
        "username",
        username
    );

    formData.append(
        "password",
        password
    );

    const response = await api.post(
        "/auth/login",
        formData,
        {
            headers: {
                "Content-Type":
                    "application/x-www-form-urlencoded"
            }
        }
    );

    return response.data;
};


// ============================================================
// TICKETS
// ============================================================

export const getTickets = async () =>
    (await api.get("/tickets")).data;


export const getTicket = async (
    ticketId
) =>
    (
        await api.get(
            `/tickets/${ticketId}`
        )
    ).data;


export const investigateTicket = async (
    ticketId
) =>
    (
        await api.post(
            `/tickets/${ticketId}/investigate`
        )
    ).data;


export const approveTicket = async (
    ticketId,
    comment
) =>
    (
        await api.post(
            `/tickets/${ticketId}/approve`,
            { comment }
        )
    ).data;


export const rejectTicket = async (
    ticketId,
    comment
) =>
    (
        await api.post(
            `/tickets/${ticketId}/reject`,
            { comment }
        )
    ).data;


export const investigateMore = async (
    ticketId,
    comment
) =>
    (
        await api.post(
            `/tickets/${ticketId}/investigate-more`,
            { comment }
        )
    ).data;


export const resolveTicket = async (
    ticketId
) =>
    (
        await api.post(
            `/tickets/${ticketId}/resolve`
        )
    ).data;


// ============================================================
// EVALUATION
// ============================================================

export const getTicketEvaluation = async (
    ticketId
) =>
    (
        await api.get(
            `/tickets/${ticketId}/evaluation`
        )
    ).data;


// ============================================================
// DASHBOARD
// ============================================================

export const getDashboardMetrics = async () =>
    (
        await api.get(
            "/dashboard/metrics"
        )
    ).data;


// ============================================================
// LOGOUT
// ============================================================

export const logout = () => {

    localStorage.removeItem(
        "access_token"
    );

    localStorage.removeItem(
        "username"
    );

    localStorage.removeItem(
        "role"
    );
};


export default api;