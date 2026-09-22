import { useNavigate } from "react-router-dom";

import {
    LayoutDashboard,
    Ticket,
    LogOut,
    ShieldCheck
} from "lucide-react";


function Sidebar() {

    const navigate = useNavigate();

    const username =
        localStorage.getItem("username") || "User";

    const role =
        localStorage.getItem("role") || "viewer";


    const handleLogout = () => {

        localStorage.removeItem("access_token");
        localStorage.removeItem("username");
        localStorage.removeItem("role");

        navigate("/login", {
            replace: true
        });
    };


    const formattedRole = role
        .replace(/_/g, " ")
        .replace(/\b\w/g, (char) =>
            char.toUpperCase()
        );


    return (

        <aside className="sidebar">

            {/* BRAND */}

            <div className="sidebar-header">

                <div className="sidebar-logo">
                    <ShieldCheck size={24} />
                </div>

                <div>
                    <h2>
                        AI Support
                    </h2>

                    <span>
                        Ticket Intelligence
                    </span>
                </div>

            </div>


            {/* NAVIGATION */}

            <nav className="sidebar-nav">

                <button
                    className="sidebar-link"
                    onClick={() => navigate("/")}
                >
                    <LayoutDashboard size={19} />

                    <span>
                        Dashboard
                    </span>
                </button>


                <button
                    className="sidebar-link"
                    onClick={() => navigate("/")}
                >
                    <Ticket size={19} />

                    <span>
                        Tickets
                    </span>
                </button>

            </nav>


            {/* USER */}

            <div className="sidebar-bottom">

                <div className="sidebar-user">

                    <div className="sidebar-avatar">
                        {username
                            .charAt(0)
                            .toUpperCase()}
                    </div>


                    <div className="sidebar-user-info">

                        <strong>
                            {username}
                        </strong>

                        <span>
                            {formattedRole}
                        </span>

                    </div>

                </div>


                {/* LOGOUT */}

                <button
                    className="sidebar-logout"
                    onClick={handleLogout}
                >

                    <LogOut size={18} />

                    <span>
                        Logout
                    </span>

                </button>

            </div>

        </aside>
    );
}


export default Sidebar;