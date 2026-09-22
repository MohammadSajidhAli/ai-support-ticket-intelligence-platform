import json
from pathlib import Path

import chromadb
import ollama

from sqlalchemy.orm import Session

from database.database import SessionLocal

from models.ticket import TicketDB

from services.rag_service import (
    retrieve_documents,
    rerank_documents
)

BASE_DIR = Path(__file__).resolve().parent.parent

CHROMA_PATH = BASE_DIR / "chroma_db"

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

BASE_DIR = Path(__file__).resolve().parent.parent

OPERATIONAL_DATA_PATH = (
    BASE_DIR / "operational_data"
)


def search_logs(query: str = ""):
    """
    Search application logs for relevant information.
    """

    logs_file = OPERATIONAL_DATA_PATH / "logs.txt"

    if not logs_file.exists():
        return []

    content = logs_file.read_text(
        encoding="utf-8"
    )

    if not query:
        return content

    query_words = set(
        query.lower().split()
    )

    matching_lines = []

    for line in content.splitlines():

        line_words = set(
            line.lower().split()
        )

        if query_words & line_words:
            matching_lines.append(line)

    return matching_lines


def get_service_status():

    status_file = (
        OPERATIONAL_DATA_PATH
        / "service_status.txt"
    )

    if not status_file.exists():
        return "Service status information unavailable."

    return status_file.read_text(
        encoding="utf-8"
    )


def get_deployment_info():

    deployment_file = (
        OPERATIONAL_DATA_PATH
        / "deployments.txt"
    )

    if not deployment_file.exists():
        return "Deployment information unavailable."

    return deployment_file.read_text(
        encoding="utf-8"
    )

def generate_embedding(
    text: str
):

    response = ollama.embed(

        model="nomic-embed-text",

        input=text
    )

    return response[
        "embeddings"
    ][0]

# ============================================================
# TOOL 1
# SEARCH KNOWLEDGE BASE
# ============================================================

def search_knowledge_base(
    query: str
):

    documents = retrieve_documents(
        query=query,
        top_k=5,
        distance_threshold=0.80
    )

    documents = rerank_documents(
        query=query,
        documents=documents
    )

    documents = documents[:3]

    results = []

    for document in documents:

        results.append(
            {
                "source": document["source"],
                "content": document["content"],
                "score": document["rerank_score"]
            }
        )

    return results


# ============================================================
# TOOL 2
# GET TICKET
# ============================================================

def get_ticket(
    ticket_id: int
):

    db: Session = SessionLocal()

    try:

        ticket = (
            db.query(TicketDB)
            .filter(
                TicketDB.id == ticket_id
            )
            .first()
        )

        if ticket is None:

            return {
                "error": "Ticket not found"
            }

        return {
    "id": ticket.id,

    "customer": ticket.customer,

    "issue": ticket.issue,

    "priority": ticket.priority,

    "status": ticket.status
}

    finally:

        db.close()


# ============================================================
# TOOL 3
# SEARCH SIMILAR TICKETS
# ============================================================

def search_similar_tickets(
    issue: str,
    limit: int = 5,
    exclude_ticket_id: int | None = None
):

    db: Session = SessionLocal()

    try:

        # ====================================================
        # GET TICKETS FROM DATABASE
        # ====================================================

        tickets = (
            db.query(TicketDB)
            .all()
        )


        # ====================================================
        # GET TICKET VECTOR COLLECTION
        # ====================================================

        ticket_collection = (
            chroma_client.get_or_create_collection(
                name="support_tickets"
            )
        )


        # ====================================================
        # CLEAR OLD VECTOR INDEX
        # ====================================================

        existing = ticket_collection.get()

        existing_ids = existing.get(
            "ids",
            []
        )

        if existing_ids:

            ticket_collection.delete(
                ids=existing_ids
            )


        # ====================================================
        # INDEX CURRENT DATABASE TICKETS
        # ====================================================

        for ticket in tickets:

            ticket_text = (
                f"Customer: {ticket.customer}\n"
                f"Issue: {ticket.issue}\n"
                f"Priority: {ticket.priority}\n"
                f"Status: {ticket.status}"
            )


            embedding = generate_embedding(
                ticket_text
            )


            ticket_collection.upsert(

                ids=[
                    f"ticket-{ticket.id}"
                ],

                documents=[
                    ticket_text
                ],

                embeddings=[
                    embedding
                ],

                metadatas=[
                    {
                        "ticket_id":
                            ticket.id,

                        "customer":
                            ticket.customer,

                        "priority":
                            ticket.priority,

                        "status":
                            ticket.status
                    }
                ]
            )


        # ====================================================
        # NO OTHER TICKETS
        # ====================================================

        if (
            exclude_ticket_id is not None
            and len(tickets) <= 1
        ):

            return []


        # ====================================================
        # QUERY EMBEDDING
        # ====================================================

        query_embedding = generate_embedding(
            issue
        )


        # ====================================================
        # SEMANTIC SEARCH
        # ====================================================

        results = ticket_collection.query(

            query_embeddings=[
                query_embedding
            ],

            n_results=min(
                limit + 1,
                len(tickets)
            )
        )


        documents = results.get(
            "documents",
            [[]]
        )[0]

        metadatas = results.get(
            "metadatas",
            [[]]
        )[0]

        distances = results.get(
            "distances",
            [[]]
        )[0]


        similar_tickets = []


        # ====================================================
        # BUILD RESULTS
        # ====================================================

        for document, metadata, distance in zip(
            documents,
            metadatas,
            distances
        ):

            ticket_id = metadata[
                "ticket_id"
            ]


            # ----------------------------------------------
            # Exclude current ticket
            # ----------------------------------------------

            if (
                exclude_ticket_id is not None
                and
                ticket_id == exclude_ticket_id
            ):

                continue


            similarity = 1 / (
                1 + distance
            )


            similar_tickets.append(

                {
                    "ticket_id":
                        ticket_id,

                    "customer":
                        metadata["customer"],

                    "priority":
                        metadata["priority"],

                    "status":
                        metadata["status"],

                    "issue":
                        document,

                    "similarity":
                        round(
                            similarity,
                            4
                        )
                }
            )


            if len(similar_tickets) >= limit:

                break


        return similar_tickets


    finally:

        db.close()# ============================================================
# TEST TOOLS
# ============================================================

if __name__ == "__main__":

    print("\n")
    print("=" * 60)
    print("TESTING TOOL CALLING FUNCTIONS")
    print("=" * 60)

    print("\n")
    print("TOOL 1: SEARCH KNOWLEDGE BASE")

    result = search_knowledge_base(
        "500 errors after deployment"
    )

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print("\n")
    print("TOOL 2: GET TICKET")

    result = get_ticket(1)

    print(
        json.dumps(
            result,
            indent=2
        )
    )

    print("\n")
    print("TOOL 3: SEARCH SIMILAR TICKETS")

    result = search_similar_tickets(
    issue="API returning 500 errors",
    exclude_ticket_id=1
)

    print(
        json.dumps(
            result,
            indent=2
        )
    )