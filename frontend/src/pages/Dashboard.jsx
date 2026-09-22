import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
    Activity,
    AlertCircle,
    CheckCircle,
    Clock3,
    FileText,
    Gauge,
    Search,
    ShieldCheck,
    Ticket,
    TrendingUp,
    XCircle
} from "lucide-react";

import {
    getTickets,
    getDashboardMetrics
} from "../services/api";

import Sidebar from "../components/Sidebar";


function Dashboard() {

    const navigate = useNavigate();

    const [tickets, setTickets] = useState([]);
    const [metrics, setMetrics] = useState(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");


    // ============================================================
    // LOAD DASHBOARD DATA
    // ============================================================

    const loadDashboard = async () => {

        try {

            setLoading(true);
            setError("");

            const [ticketsData, metricsData] =
                await Promise.all([
                    getTickets(),
                    getDashboardMetrics()
                ]);

            setTickets(ticketsData || []);
            setMetrics(metricsData);

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Unable to load dashboard."
            );

        } finally {

            setLoading(false);

        }
    };


    useEffect(() => {

        loadDashboard();

    }, []);


    // ============================================================
    // HELPERS
    // ============================================================

    const statusCount =
        metrics?.tickets?.by_status || {};

    const totalTickets =
        metrics?.tickets?.total || tickets.length;

    const openTickets =
        statusCount.open || 0;

    const resolvedTickets =
        statusCount.resolved || 0;

    const investigatedTickets =
        metrics?.tickets?.investigated || 0;

    const approvedTickets =
        metrics?.tickets?.approved || 0;

    const rejectedTickets =
        metrics?.tickets?.rejected || 0;

    const evaluationCount =
        metrics?.evaluation?.count || 0;

    const averageDuration =
        metrics?.evaluation?.average_duration_ms || 0;

    const averageConfidence =
        metrics?.evaluation?.average_confidence || 0;

    const averageScore =
        metrics?.evaluation?.average_overall_score || 0;

    const successRate =
        metrics?.evaluation?.success_rate || 0;


    // ============================================================
    // LOADING
    // ============================================================

    if (loading) {

        return (

            <div className="app-layout">

                <Sidebar />

                <main className="main-content">

                    <div className="page-loading">
                        Loading dashboard...
                    </div>

                </main>

            </div>

        );

    }


    // ============================================================
    // RENDER
    // ============================================================

    return (

        <div className="app-layout">

            <Sidebar />


            <main className="main-content">

                <div className="dashboard-page">

                    {/* HEADER */}

                    <div className="dashboard-header">

                        <div>

                            <span className="section-eyebrow">
                                OPERATIONS
                            </span>

                            <h1>
                                Support Intelligence Dashboard
                            </h1>

                            <p>
                                Monitor tickets, AI investigations,
                                human approvals and resolution activity.
                            </p>

                        </div>


                        <button
                            className="secondary-button"
                            onClick={loadDashboard}
                        >
                            <Activity size={17} />
                            Refresh
                        </button>

                    </div>


                    {/* ERROR */}

                    {error && (

                        <div className="error-banner">

                            <XCircle size={18} />

                            <span>
                                {error}
                            </span>

                        </div>

                    )}


                    {/* TICKET METRICS */}

                    <div className="dashboard-stat-grid">

                        <div className="dashboard-stat-card">

                            <div className="dashboard-stat-icon">
                                <Ticket size={20} />
                            </div>

                            <div>

                                <span>
                                    Total Tickets
                                </span>

                                <strong>
                                    {totalTickets}
                                </strong>

                            </div>

                        </div>


                        <div className="dashboard-stat-card">

                            <div className="dashboard-stat-icon">
                                <AlertCircle size={20} />
                            </div>

                            <div>

                                <span>
                                    Open Tickets
                                </span>

                                <strong>
                                    {openTickets}
                                </strong>

                            </div>

                        </div>


                        <div className="dashboard-stat-card">

                            <div className="dashboard-stat-icon">
                                <Search size={20} />
                            </div>

                            <div>

                                <span>
                                    Investigated
                                </span>

                                <strong>
                                    {investigatedTickets}
                                </strong>

                            </div>

                        </div>


                        <div className="dashboard-stat-card">

                            <div className="dashboard-stat-icon">
                                <CheckCircle size={20} />
                            </div>

                            <div>

                                <span>
                                    Resolved
                                </span>

                                <strong>
                                    {resolvedTickets}
                                </strong>

                            </div>

                        </div>

                    </div>


                    {/* AI OBSERVABILITY */}

                    <div className="dashboard-section">

                        <div className="dashboard-section-header">

                            <div>

                                <span className="section-eyebrow">
                                    AI OBSERVABILITY
                                </span>

                                <h2>
                                    Investigation Performance
                                </h2>

                            </div>

                            <Gauge size={22} />

                        </div>


                        <div className="observability-grid">

                            <div className="observability-card">

                                <div className="observability-card-header">

                                    <span>
                                        Average Investigation Time
                                    </span>

                                    <Clock3 size={18} />

                                </div>

                                <strong>
                                    {Math.round(averageDuration)} ms
                                </strong>

                                <small>
                                    Across {evaluationCount} evaluations
                                </small>

                            </div>


                            <div className="observability-card">

                                <div className="observability-card-header">

                                    <span>
                                        Average AI Confidence
                                    </span>

                                    <TrendingUp size={18} />

                                </div>

                                <strong>
                                    {Math.round(
                                        averageConfidence * 100
                                    )}%
                                </strong>

                                <small>
                                    Investigation confidence
                                </small>

                            </div>


                            <div className="observability-card">

                                <div className="observability-card-header">

                                    <span>
                                        Average Evaluation Score
                                    </span>

                                    <Gauge size={18} />

                                </div>

                                <strong>
                                    {Math.round(
                                        averageScore * 100
                                    )}%
                                </strong>

                                <small>
                                    Structural quality score
                                </small>

                            </div>


                            <div className="observability-card">

                                <div className="observability-card-header">

                                    <span>
                                        Evaluation Success Rate
                                    </span>

                                    <CheckCircle size={18} />

                                </div>

                                <strong>
                                    {Math.round(
                                        successRate * 100
                                    )}%
                                </strong>

                                <small>
                                    Successful evaluations
                                </small>

                            </div>

                        </div>

                    </div>


                    {/* WORKFLOW */}

                    <div className="dashboard-two-column">

                        <div className="dashboard-panel">

                            <div className="dashboard-panel-header">

                                <div>

                                    <span className="section-eyebrow">
                                        WORKFLOW
                                    </span>

                                    <h2>
                                        Ticket Lifecycle
                                    </h2>

                                </div>

                            </div>


                            <div className="workflow-metrics">

                                <div className="workflow-metric">

                                    <Search size={17} />

                                    <div>

                                        <span>
                                            Investigated
                                        </span>

                                        <strong>
                                            {investigatedTickets}
                                        </strong>

                                    </div>

                                </div>


                                <div className="workflow-metric">

                                    <ShieldCheck size={17} />

                                    <div>

                                        <span>
                                            Approved
                                        </span>

                                        <strong>
                                            {approvedTickets}
                                        </strong>

                                    </div>

                                </div>


                                <div className="workflow-metric">

                                    <XCircle size={17} />

                                    <div>

                                        <span>
                                            Rejected
                                        </span>

                                        <strong>
                                            {rejectedTickets}
                                        </strong>

                                    </div>

                                </div>


                                <div className="workflow-metric">

                                    <CheckCircle size={17} />

                                    <div>

                                        <span>
                                            Resolved
                                        </span>

                                        <strong>
                                            {resolvedTickets}
                                        </strong>

                                    </div>

                                </div>

                            </div>

                        </div>


                        {/* STATUS */}

                        <div className="dashboard-panel">

                            <div className="dashboard-panel-header">

                                <div>

                                    <span className="section-eyebrow">
                                        STATUS
                                    </span>

                                    <h2>
                                        Ticket Distribution
                                    </h2>

                                </div>

                            </div>


                            <div className="status-bars">

                                <div className="status-bar-row">

                                    <div>

                                        <span>
                                            Open
                                        </span>

                                        <strong>
                                            {openTickets}
                                        </strong>

                                    </div>

                                    <div className="status-bar">

                                        <div
                                            style={{
                                                width: `${totalTickets
                                                    ? (openTickets / totalTickets) * 100
                                                    : 0
                                                    }%`
                                            }}
                                        />

                                    </div>

                                </div>


                                <div className="status-bar-row">

                                    <div>

                                        <span>
                                            Resolved
                                        </span>

                                        <strong>
                                            {resolvedTickets}
                                        </strong>

                                    </div>

                                    <div className="status-bar">

                                        <div
                                            style={{
                                                width: `${totalTickets
                                                    ? (resolvedTickets / totalTickets) * 100
                                                    : 0
                                                    }%`
                                            }}
                                        />

                                    </div>

                                </div>

                            </div>

                        </div>

                    </div>


                    {/* RECENT TICKETS */}

                    <div className="dashboard-section">

                        <div className="dashboard-section-header">

                            <div>

                                <span className="section-eyebrow">
                                    SUPPORT QUEUE
                                </span>

                                <h2>
                                    Recent Tickets
                                </h2>

                            </div>

                            <FileText size={22} />

                        </div>


                        {tickets.length === 0 ? (

                            <div className="dashboard-empty">
                                No tickets found.
                            </div>

                        ) : (

                            <div className="ticket-table">

                                <div className="ticket-table-header">

                                    <span>
                                        Ticket
                                    </span>

                                    <span>
                                        Customer
                                    </span>

                                    <span>
                                        Priority
                                    </span>

                                    <span>
                                        Status
                                    </span>

                                    <span>
                                        Investigation
                                    </span>

                                </div>


                                {tickets
                                    .slice()
                                    .reverse()
                                    .slice(0, 8)
                                    .map((ticket) => (

                                        <button
                                            className="ticket-table-row"
                                            key={ticket.id}
                                            onClick={() =>
                                                navigate(
                                                    `/tickets/${ticket.id}`
                                                )
                                            }
                                        >

                                            <span className="ticket-id">
                                                #{ticket.id}
                                            </span>

                                            <span>
                                                {ticket.customer}
                                            </span>

                                            <span>

                                                <span
                                                    className={`priority ${ticket.priority}`}
                                                >
                                                    {ticket.priority}
                                                </span>

                                            </span>

                                            <span>

                                                <span
                                                    className={`status ${ticket.status}`}
                                                >
                                                    {ticket.status}
                                                </span>

                                            </span>

                                            <span>

                                                {ticket.investigation ? (

                                                    <span className="investigation-ready">

                                                        <CheckCircle size={14} />

                                                        Completed

                                                    </span>

                                                ) : (

                                                    <span className="investigation-pending">
                                                        Pending
                                                    </span>

                                                )}

                                            </span>

                                        </button>

                                    ))}

                            </div>

                        )}

                    </div>

                </div>

            </main>

        </div>
    );
}


export default Dashboard;