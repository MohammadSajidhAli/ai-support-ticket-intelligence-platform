import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";

import {
    canInvestigate,
    canApprove,
    canResolve
} from "../utils/permissions";

import {
    ArrowLeft,
    Search,
    CheckCircle,
    XCircle,
    ShieldCheck,
    Play,
    Activity,
    FileText,
    Bot
} from "lucide-react";

import {
    getTicket,
    investigateTicket,
    approveTicket,
    rejectTicket,
    investigateMore,
    resolveTicket,
    getTicketEvaluation
} from "../services/api";

import Sidebar from "../components/Sidebar";


function TicketDetails() {

    const { ticketId } = useParams();
    const navigate = useNavigate();

    // ============================================================
    // ROLE PERMISSIONS
    // ============================================================

    const allowInvestigate = canInvestigate();
    const allowApprove = canApprove();
    const allowResolve = canResolve();


    // ============================================================
    // STATE
    // ============================================================

    const [evaluation, setEvaluation] = useState(null);

    const [ticket, setTicket] = useState(null);
    const [investigation, setInvestigation] = useState(null);

    const [loading, setLoading] = useState(true);
    const [investigating, setInvestigating] = useState(false);
    const [actionLoading, setActionLoading] = useState(false);

    const [error, setError] = useState("");
    const [resolutionResult, setResolutionResult] = useState(null);


    // ============================================================
    // LOAD TICKET
    // ============================================================

    const loadTicket = async () => {

        try {

            setLoading(true);
            setError("");

            const data = await getTicket(ticketId);

            setTicket(data);

            if (data.investigation) {
                setInvestigation(data.investigation);
            } else {
                setInvestigation(null);
            }

            // ====================================================
            // LOAD EVALUATION
            // ====================================================

            try {

                const evaluationData =
                    await getTicketEvaluation(ticketId);

                setEvaluation(evaluationData);

            } catch (evaluationError) {

                // 404 is expected when investigation
                // has not been performed yet.

                setEvaluation(null);

            }

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Unable to load ticket."
            );

        } finally {

            setLoading(false);

        }
    };


    useEffect(() => {

        loadTicket();

    }, [ticketId]);


    // ============================================================
    // RUN INVESTIGATION
    // ============================================================

    const handleInvestigate = async () => {

        if (
            investigating ||
            !allowInvestigate ||
            investigation
        ) {
            return;
        }

        try {

            setInvestigating(true);
            setError("");

            const result =
                await investigateTicket(ticketId);

            if (result?.investigation) {

                setInvestigation(
                    result.investigation
                );

            }

            await loadTicket();

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Failed to run AI investigation."
            );

        } finally {

            setInvestigating(false);

        }
    };


    // ============================================================
    // APPROVE
    // ============================================================

    const handleApprove = async () => {

        if (!allowApprove) {
            return;
        }

        try {

            setActionLoading(true);
            setError("");

            const result =
                await approveTicket(
                    ticketId,
                    "Evidence is sufficient"
                );

            if (result?.investigation) {

                setInvestigation(
                    result.investigation
                );

            }

            await loadTicket();

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Failed to approve investigation."
            );

        } finally {

            setActionLoading(false);

        }
    };


    // ============================================================
    // REJECT
    // ============================================================

    const handleReject = async () => {

        if (!allowApprove) {
            return;
        }

        try {

            setActionLoading(true);
            setError("");

            const result =
                await rejectTicket(
                    ticketId,
                    "Evidence is insufficient"
                );

            if (result?.investigation) {

                setInvestigation(
                    result.investigation
                );

            }

            await loadTicket();

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Failed to reject investigation."
            );

        } finally {

            setActionLoading(false);

        }
    };


    // ============================================================
    // MORE INVESTIGATION
    // ============================================================

    const handleInvestigateMore = async () => {

        if (!allowInvestigate) {
            return;
        }

        try {

            setActionLoading(true);
            setError("");

            const result =
                await investigateMore(
                    ticketId,
                    "Need additional supporting evidence."
                );

            if (result?.investigation) {

                setInvestigation(
                    result.investigation
                );

            }

            await loadTicket();

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Failed to request more investigation."
            );

        } finally {

            setActionLoading(false);

        }
    };


    // ============================================================
    // RESOLVE
    // ============================================================

    const handleResolve = async () => {

        if (!allowResolve) {
            return;
        }

        try {

            setActionLoading(true);
            setError("");

            const result =
                await resolveTicket(ticketId);

            setResolutionResult(result);

            await loadTicket();

        } catch (err) {

            console.error(err);

            setError(
                err.response?.data?.detail ||
                "Failed to execute resolution."
            );

        } finally {

            setActionLoading(false);

        }
    };


    // ============================================================
    // LOADING
    // ============================================================

    if (loading) {

        return (

            <div className="app-layout">

                <Sidebar />

                <main className="main-content">

                    <div className="page-loading">
                        Loading ticket...
                    </div>

                </main>

            </div>

        );
    }


    // ============================================================
    // ERROR / NO TICKET
    // ============================================================

    if (!ticket) {

        return (

            <div className="app-layout">

                <Sidebar />

                <main className="main-content">

                    <div className="page-loading">

                        <h2>
                            Ticket not found
                        </h2>

                        <button
                            className="primary-button"
                            onClick={() => navigate("/")}
                        >
                            Back to Dashboard
                        </button>

                    </div>

                </main>

            </div>

        );
    }


    // ============================================================
    // CURRENT INVESTIGATION STATE
    // ============================================================

    const approval =
        investigation?.approval;

    const isApproved =
        approval?.status === "approved";

    const isRejected =
        approval?.status === "rejected";

    const hasInvestigation =
        !!investigation;

    const isResolved =
        ticket.status === "resolved";


    // ============================================================
    // RENDER
    // ============================================================

    return (

        <div className="app-layout">

            <Sidebar />

            <main className="main-content">

                <div className="ticket-page">

                    {/* ====================================================
                        HEADER
                    ==================================================== */}

                    <div className="ticket-header">

                        <button
                            className="back-button"
                            onClick={() => navigate("/")}
                        >
                            <ArrowLeft size={17} />
                            Back to Dashboard
                        </button>


                        <div className="ticket-heading">

                            <div>

                                <span className="ticket-number">
                                    Ticket #{ticket.id}
                                </span>

                                <h1>
                                    {ticket.customer}
                                </h1>

                                <p>
                                    {ticket.issue}
                                </p>

                            </div>


                            <div className="ticket-badges">

                                <span
                                    className={`priority ${ticket.priority}`}
                                >
                                    {ticket.priority}
                                </span>

                                <span
                                    className={`status ${ticket.status}`}
                                >
                                    {ticket.status}
                                </span>

                            </div>

                        </div>

                    </div>


                    {/* ====================================================
                        ERROR
                    ==================================================== */}

                    {error && (

                        <div className="error-banner">

                            <XCircle size={18} />

                            <span>
                                {error}
                            </span>

                        </div>

                    )}


                    {/* ====================================================
                        TOP INFORMATION
                    ==================================================== */}

                    <div className="ticket-grid">

                        {/* TICKET INFORMATION */}

                        <div className="detail-card">

                            <div className="card-title">

                                <FileText size={19} />

                                Ticket Information

                            </div>


                            <div className="info-list">

                                <div className="info-row">

                                    <span>
                                        Customer
                                    </span>

                                    <strong>
                                        {ticket.customer}
                                    </strong>

                                </div>


                                <div className="info-row">

                                    <span>
                                        Priority
                                    </span>

                                    <strong>
                                        {ticket.priority}
                                    </strong>

                                </div>


                                <div className="info-row">

                                    <span>
                                        Status
                                    </span>

                                    <strong>
                                        {ticket.status}
                                    </strong>

                                </div>


                                <div className="info-row">

                                    <span>
                                        Ticket ID
                                    </span>

                                    <strong>
                                        #{ticket.id}
                                    </strong>

                                </div>

                            </div>

                        </div>


                        {/* HUMAN APPROVAL */}

                        <div className="detail-card">

                            <div className="card-title">

                                <ShieldCheck size={19} />

                                Human Approval

                            </div>


                            {!hasInvestigation && (

                                <div className="approval-empty">

                                    <ShieldCheck size={30} />

                                    <strong>
                                        Waiting for investigation
                                    </strong>

                                    <span>
                                        Run the AI investigation before
                                        reviewing the resolution.
                                    </span>

                                </div>

                            )}


                            {hasInvestigation &&
                                approval?.status === "pending" && (

                                    <div className="approval-empty">

                                        <ShieldCheck size={30} />

                                        <strong>
                                            Awaiting human review
                                        </strong>

                                        <span>
                                            Review the AI evidence
                                            and investigation.
                                        </span>

                                    </div>

                                )}


                            {hasInvestigation &&
                                approval?.status === "approved" && (

                                    <div className="approval-details">

                                        <div className="approval-badge">

                                            <CheckCircle size={17} />

                                            Approved

                                        </div>


                                        <div className="approval-row">

                                            <span>
                                                Reviewer
                                            </span>

                                            <strong>
                                                {approval.reviewer}
                                            </strong>

                                        </div>


                                        {approval.comment && (

                                            <div className="approval-comment">

                                                {approval.comment}

                                            </div>

                                        )}

                                    </div>

                                )}


                            {hasInvestigation &&
                                approval?.status === "rejected" && (

                                    <div className="approval-details">

                                        <div className="approval-badge rejected">

                                            <XCircle size={17} />

                                            Rejected

                                        </div>


                                        <div className="approval-row">

                                            <span>
                                                Reviewer
                                            </span>

                                            <strong>
                                                {approval.reviewer}
                                            </strong>

                                        </div>


                                        {approval.comment && (

                                            <div className="approval-comment">

                                                {approval.comment}

                                            </div>

                                        )}

                                    </div>

                                )}

                        </div>

                    </div>


                    {/* ====================================================
                        AI INVESTIGATION
                    ==================================================== */}

                    <div className="investigation-card">

                        <div className="investigation-header">

                            <div>

                                <div className="card-title">

                                    <Bot size={19} />

                                    AI Investigation

                                </div>

                                <p>
                                    AI-assisted analysis using
                                    knowledge-base and operational evidence.
                                </p>

                            </div>


                            {allowInvestigate && (

                                <button
                                    className="primary-button"
                                    onClick={handleInvestigate}
                                    disabled={
                                        investigating ||
                                        hasInvestigation ||
                                        isResolved
                                    }
                                >

                                    <Search size={17} />

                                    {investigating
                                        ? "Investigating..."
                                        : hasInvestigation
                                            ? "Investigation Completed"
                                            : "Run Investigation"
                                    }

                                </button>

                            )}

                        </div>


                        {!hasInvestigation && (

                            <div className="empty-investigation">

                                <Bot size={42} />

                                <h3>
                                    No investigation loaded
                                </h3>

                                <p>
                                    {allowInvestigate
                                        ? "Run the AI investigation to analyze this ticket and collect supporting evidence."
                                        : "This ticket has not been investigated yet. Your role has view-only access."
                                    }
                                </p>

                            </div>

                        )}


                        {hasInvestigation && (

                            <div className="investigation-content">

                                {/* SUMMARY */}

                                <div className="investigation-section">

                                    <h3>
                                        Summary
                                    </h3>

                                    <p>
                                        {investigation.summary}
                                    </p>

                                </div>


                                {/* ROOT CAUSE */}

                                <div className="root-cause-box">

                                    <div className="section-label">

                                        <Activity size={17} />

                                        Root Cause Hypothesis

                                    </div>

                                    <p>
                                        {investigation.root_cause_hypothesis}
                                    </p>

                                </div>


                                {/* CONFIDENCE */}

                                <div className="confidence-section">

                                    <div className="confidence-header">

                                        <span>
                                            AI Confidence
                                        </span>

                                        <strong>
                                            {Math.round(
                                                investigation.confidence * 100
                                            )}
                                            %
                                        </strong>

                                    </div>

                                    <div className="confidence-bar">

                                        <div
                                            className="confidence-fill"
                                            style={{
                                                width: `${investigation.confidence * 100}%`
                                            }}
                                        />

                                    </div>

                                </div>


                                {/* EVIDENCE */}

                                <div className="investigation-section">

                                    <div className="section-heading">

                                        <h3>
                                            Evidence
                                        </h3>

                                        <span>
                                            {investigation.evidence?.length || 0}
                                            {" "}items
                                        </span>

                                    </div>


                                    <div className="evidence-list">

                                        {investigation.evidence?.map(
                                            (item, index) => {

                                                const source =
                                                    item?.source ||
                                                    "Investigation Evidence";

                                                const finding =
                                                    item?.finding ||
                                                    item?.content ||
                                                    item?.description ||
                                                    "No evidence details available.";

                                                return (

                                                    <div
                                                        className="evidence-item"
                                                        key={index}
                                                    >

                                                        <div className="evidence-icon">

                                                            <Activity size={17} />

                                                        </div>


                                                        <div className="evidence-body">

                                                            <div className="evidence-source">

                                                                <strong>
                                                                    {source}
                                                                </strong>

                                                                <span>
                                                                    Evidence #{index + 1}
                                                                </span>

                                                            </div>


                                                            <p>
                                                                {finding}
                                                            </p>

                                                        </div>

                                                    </div>

                                                );

                                            }
                                        )}

                                    </div>

                                </div>


                                {/* RECOMMENDED ACTIONS */}

                                <div className="investigation-section">

                                    <h3>
                                        Recommended Actions
                                    </h3>


                                    <div className="recommendation-list">

                                        {investigation.recommended_actions?.map(
                                            (action, index) => (

                                                <div
                                                    className="recommendation-item"
                                                    key={index}
                                                >

                                                    <CheckCircle size={17} />

                                                    <span>
                                                        {action}
                                                    </span>

                                                </div>

                                            )
                                        )}

                                    </div>

                                </div>


                                {/* SOURCES */}

                                <div className="investigation-section">

                                    <h3>
                                        Knowledge Sources
                                    </h3>

                                    <div className="source-list">

                                        {investigation.sources?.map(
                                            (source, index) => (

                                                <span
                                                    className="source-tag"
                                                    key={index}
                                                >
                                                    {source}
                                                </span>

                                            )
                                        )}

                                    </div>

                                </div>

                            </div>

                        )}

                    </div>


                    {/* ====================================================
                        AI EVALUATION / OBSERVABILITY
                    ==================================================== */}

                    {evaluation && (

                        <section className="details-section evaluation-section">

                            <div className="section-header">

                                <div>

                                    <span className="section-eyebrow">
                                        OBSERVABILITY
                                    </span>

                                    <div className="card-title">
                                        <Activity size={19} />
                                        AI Investigation Evaluation
                                    </div>

                                    <p>
                                        Structural metrics for the AI investigation.
                                    </p>

                                </div>


                                <div className="evaluation-score">

                                    <span>
                                        Overall Score
                                    </span>

                                    <strong>
                                        {Math.round(
                                            evaluation.scores.overall * 100
                                        )}%
                                    </strong>

                                </div>

                            </div>


                            {/* PERFORMANCE METRICS */}

                            <div className="evaluation-grid">

                                <div className="evaluation-card">

                                    <span>
                                        Investigation Time
                                    </span>

                                    <strong>
                                        {Math.round(
                                            evaluation.duration_ms
                                        )} ms
                                    </strong>

                                </div>


                                <div className="evaluation-card">

                                    <span>
                                        Evidence
                                    </span>

                                    <strong>
                                        {evaluation.evidence_count}
                                    </strong>

                                </div>


                                <div className="evaluation-card">

                                    <span>
                                        Knowledge Sources
                                    </span>

                                    <strong>
                                        {evaluation.unique_source_count}
                                    </strong>

                                </div>


                                <div className="evaluation-card">

                                    <span>
                                        Recommended Actions
                                    </span>

                                    <strong>
                                        {evaluation.recommended_action_count}
                                    </strong>

                                </div>


                                <div className="evaluation-card">

                                    <span>
                                        AI Confidence
                                    </span>

                                    <strong>
                                        {Math.round(
                                            evaluation.confidence * 100
                                        )}%
                                    </strong>

                                </div>

                            </div>


                            {/* QUALITY SCORES */}

                            <div className="evaluation-quality">

                                <h3>
                                    Investigation Quality
                                </h3>


                                <div className="score-row">

                                    <div className="score-label">

                                        <span>
                                            Evidence Quality
                                        </span>

                                        <strong>
                                            {Math.round(
                                                evaluation.scores.evidence * 100
                                            )}%
                                        </strong>

                                    </div>

                                    <div className="score-bar">

                                        <div
                                            className="score-fill"
                                            style={{
                                                width: `${evaluation.scores.evidence * 100}%`
                                            }}
                                        />

                                    </div>

                                </div>


                                <div className="score-row">

                                    <div className="score-label">

                                        <span>
                                            Source Diversity
                                        </span>

                                        <strong>
                                            {Math.round(
                                                evaluation.scores.source_diversity * 100
                                            )}%
                                        </strong>

                                    </div>

                                    <div className="score-bar">

                                        <div
                                            className="score-fill"
                                            style={{
                                                width: `${evaluation.scores.source_diversity * 100}%`
                                            }}

                                        />

                                    </div>

                                </div>


                                <div className="score-row">

                                    <div className="score-label">

                                        <span>
                                            Actionability
                                        </span>

                                        <strong>
                                            {Math.round(
                                                evaluation.scores.actionability * 100
                                            )}%
                                        </strong>

                                    </div>

                                    <div className="score-bar">

                                        <div
                                            className="score-fill"
                                            style={{
                                                width: `${evaluation.scores.actionability * 100}%`
                                            }}
                                        />

                                    </div>

                                </div>


                                <div className="score-row">

                                    <div className="score-label">

                                        <span>
                                            Completeness
                                        </span>

                                        <strong>
                                            {Math.round(
                                                evaluation.scores.completeness * 100
                                            )}%
                                        </strong>

                                    </div>

                                    <div className="score-bar">

                                        <div
                                            className="score-fill"
                                            style={{
                                                width: `${evaluation.scores.completeness * 100}%`
                                            }}
                                        />

                                    </div>

                                </div>

                            </div>


                            <div className="evaluation-footer">

                                <span>
                                    Evaluation Status
                                </span>

                                <span className="evaluation-status">
                                    {evaluation.status}
                                </span>

                            </div>

                        </section>

                    )}


                    {/* ====================================================
                        INVESTIGATION DECISION
                    ==================================================== */}

                    <div className="action-center">

                        <div className="decision-info">

                            <div className="card-title">

                                <ShieldCheck size={20} />

                                Investigation Decision

                            </div>

                            <p>
                                Review the AI-generated investigation
                                and evidence before allowing a resolution
                                to execute.
                            </p>


                            <div className="workflow-status">

                                {/* AI INVESTIGATION */}

                                <div
                                    className={`workflow-step ${
                                        hasInvestigation
                                            ? "completed"
                                            : "current"
                                    }`}
                                >

                                    {hasInvestigation
                                        ? <CheckCircle size={16} />
                                        : <Search size={16} />
                                    }

                                    <span>
                                        AI Investigation
                                    </span>

                                </div>


                                <div className="workflow-line"></div>


                                {/* HUMAN APPROVAL */}

                                <div
                                    className={`workflow-step ${
                                        isApproved
                                            ? "completed"
                                            : hasInvestigation
                                                ? "current"
                                                : ""
                                    }`}
                                >

                                    {isApproved
                                        ? <CheckCircle size={16} />
                                        : <ShieldCheck size={16} />
                                    }

                                    <span>
                                        Human Approval
                                    </span>

                                </div>


                                <div className="workflow-line"></div>


                                {/* RESOLUTION */}

                                <div
                                    className={`workflow-step ${
                                        isResolved
                                            ? "completed"
                                            : isApproved
                                                ? "current"
                                                : ""
                                    }`}
                                >

                                    {isResolved
                                        ? <CheckCircle size={16} />
                                        : <Play size={16} />
                                    }

                                    <span>
                                        Resolution
                                    </span>

                                </div>

                            </div>

                        </div>


                        {/* ACTION BUTTONS */}

                        <div className="action-buttons">

                            {allowInvestigate && (

                                <button
                                    className="secondary-button"
                                    onClick={handleInvestigateMore}
                                    disabled={
                                        actionLoading ||
                                        !hasInvestigation ||
                                        isResolved
                                    }
                                >

                                    <Search size={17} />

                                    Investigate More

                                </button>

                            )}


                            {allowApprove && (

                                <button
                                    className="danger-button"
                                    onClick={handleReject}
                                    disabled={
                                        actionLoading ||
                                        !hasInvestigation ||
                                        isRejected ||
                                        isResolved
                                    }
                                >

                                    <XCircle size={17} />

                                    Reject

                                </button>

                            )}


                            {allowApprove && (

                                <button
                                    className="success-button"
                                    onClick={handleApprove}
                                    disabled={
                                        actionLoading ||
                                        !hasInvestigation ||
                                        isApproved ||
                                        isResolved
                                    }
                                >

                                    <CheckCircle size={17} />

                                    {isApproved
                                        ? "Approved"
                                        : "Approve Investigation"
                                    }

                                </button>

                            )}

                        </div>

                    </div>


                    {/* ====================================================
                        RESOLUTION
                    ==================================================== */}

                    <div
                        className={`resolution-card ${
                            isApproved
                                ? "resolution-ready"
                                : "resolution-locked"
                        }`}
                    >

                        <div className="resolution-info">

                            <div className="card-title">

                                {isResolved
                                    ? <CheckCircle size={20} />
                                    : isApproved
                                        ? <Play size={20} />
                                        : <ShieldCheck size={20} />
                                }

                                Resolution

                            </div>


                            <p>

                                {isResolved
                                    ? "This ticket has already been resolved."
                                    : !allowResolve
                                        ? "You have view-only access to resolution actions."
                                        : isApproved
                                            ? "Investigation approved. The recommended resolution can now be executed."
                                            : "Resolution execution is locked until a human reviewer approves the investigation."
                                }

                            </p>

                        </div>


                        {allowResolve && (

                            <button
                                className="resolve-button"
                                onClick={handleResolve}
                                disabled={
                                    actionLoading ||
                                    !isApproved ||
                                    isResolved
                                }
                            >

                                {isResolved ? (

                                    <>
                                        <CheckCircle size={17} />
                                        Resolved
                                    </>

                                ) : isApproved ? (

                                    <>
                                        <Play size={17} />
                                        Execute Resolution
                                    </>

                                ) : (

                                    <>
                                        <ShieldCheck size={17} />
                                        Approval Required
                                    </>

                                )}

                            </button>

                        )}

                    </div>


                    {/* ====================================================
                        RESOLUTION RESULT
                    ==================================================== */}

                    {resolutionResult?.success && (

                        <div className="resolution-success">

                            <div className="success-title">

                                <CheckCircle size={19} />

                                Resolution success

                            </div>


                            <p>
                                {resolutionResult.message}
                            </p>


                            {resolutionResult.action && (

                                <p>

                                    <strong>
                                        Action:
                                    </strong>{" "}

                                    {resolutionResult.action}

                                </p>

                            )}

                        </div>

                    )}

                </div>

            </main>

        </div>
    );
}


export default TicketDetails;