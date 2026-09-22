const getRole = () => {
    return localStorage.getItem("role") || "viewer";
};

export const isViewer = () => {
    return getRole() === "viewer";
};

export const canInvestigate = () => {
    const role = getRole();

    return (
        role === "support_agent" ||
        role === "admin"
    );
};

export const canApprove = () => {
    const role = getRole();

    return (
        role === "support_agent" ||
        role === "admin"
    );
};

export const canResolve = () => {
    const role = getRole();

    return (
        role === "support_agent" ||
        role === "admin"
    );
};

export const isAdmin = () => {
    return getRole() === "admin";
};