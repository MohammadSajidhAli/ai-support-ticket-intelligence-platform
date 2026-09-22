import {
    ChevronRight
} from "lucide-react";

function TicketCard({ ticket, onClick }) {

    return (
        <div
            className="ticket-card"
            onClick={onClick}
        >

            <div className="ticket-main">

                <div className="ticket-id">
                    #{ticket.id}
                </div>

                <div>

                    <h3>
                        {ticket.customer}
                    </h3>

                    <p>
                        {ticket.issue}
                    </p>

                </div>

            </div>

            <div className="ticket-meta">

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

                <ChevronRight size={18} />

            </div>

        </div>
    );
}

export default TicketCard;