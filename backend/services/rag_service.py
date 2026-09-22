from pathlib import Path

import re

import chromadb
import ollama

from services.llm_service import analyze_ticket


# ============================================================
# CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

KNOWLEDGE_BASE_PATH = BASE_DIR / "knowledge_base"
CHROMA_PATH = BASE_DIR / "chroma_db"

COLLECTION_NAME = "support_knowledge"


# ============================================================
# CHROMA DATABASE
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=CHROMA_PATH
)

collection = chroma_client.get_or_create_collection(
    name=COLLECTION_NAME
)


# ============================================================
# LOAD DOCUMENTS
# ============================================================

def load_documents():

    documents = []

    for file_path in KNOWLEDGE_BASE_PATH.glob("*.txt"):

        content = file_path.read_text(
            encoding="utf-8"
        )

        documents.append(
            {
                "source": file_path.name,
                "content": content
            }
        )

    return documents


# ============================================================
# TEXT CHUNKING
# ============================================================

def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
):

    words = text.split()

    chunks = []

    current_chunk = []

    current_length = 0

    for word in words:

        if (
            current_length
            + len(word)
            + 1
            > chunk_size
        ):

            chunks.append(
                " ".join(current_chunk)
            )

            overlap_words = []

            overlap_length = 0

            for previous_word in reversed(
                current_chunk
            ):

                if (
                    overlap_length
                    + len(previous_word)
                    + 1
                    > overlap
                ):
                    break

                overlap_words.insert(
                    0,
                    previous_word
                )

                overlap_length += (
                    len(previous_word) + 1
                )

            current_chunk = overlap_words

            current_length = overlap_length

        current_chunk.append(word)

        current_length += (
            len(word) + 1
        )

    if current_chunk:

        chunks.append(
            " ".join(current_chunk)
        )

    return chunks


# ============================================================
# LOAD + CHUNK DOCUMENTS
# ============================================================

def load_and_chunk_documents():

    documents = load_documents()

    chunks = []

    for document in documents:

        document_chunks = chunk_text(
            document["content"]
        )

        for index, chunk in enumerate(
            document_chunks
        ):

            chunks.append(
                {
                    "id": (
                        f"{document['source']}"
                        f"-{index}"
                    ),

                    "source": document["source"],

                    "content": chunk
                }
            )

    return chunks


# ============================================================
# GENERATE EMBEDDING
# ============================================================

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
# INDEX DOCUMENTS
# ============================================================

def index_documents():

    chunks = load_and_chunk_documents()

    for chunk in chunks:

        print(
            f"Embedding: {chunk['id']}"
        )

        embedding = generate_embedding(
            chunk["content"]
        )

        collection.upsert(

            ids=[
                chunk["id"]
            ],

            documents=[
                chunk["content"]
            ],

            embeddings=[
                embedding
            ],

            metadatas=[
                {
                    "source":
                    chunk["source"]
                }
            ]
        )

    print(
        f"\nIndexed {len(chunks)} "
        f"chunks into ChromaDB"
    )


# ============================================================
# RETRIEVE RELEVANT DOCUMENTS
# ============================================================

def retrieve_documents(
    query: str,
    top_k: int = 3,
    distance_threshold: float = 0.80
):
    """
    Retrieve relevant documents from ChromaDB.

    Lower distance = more similar.

    Documents with a distance greater than the
    threshold are considered weak matches and removed.
    """

    query_embedding = generate_embedding(
        query
    )

    results = collection.query(
        query_embeddings=[
            query_embedding
        ],
        n_results=top_k
    )

    retrieved_documents = []

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

    for document, metadata, distance in zip(
        documents,
        metadatas,
        distances
    ):

        # Ignore weak matches
        if distance > distance_threshold:
            continue

        retrieved_documents.append(
            {
                "content": document,

                "source":
                metadata["source"],

                "distance":
                distance
            }
        )

    return retrieved_documents


def tokenize(text: str):
    """
    Convert text into normalized words.
    """

    return set(
        re.findall(
            r"\b[a-zA-Z0-9]+\b",
            text.lower()
        )
    )


def rerank_documents(
    query: str,
    documents: list[dict]
):
    """
    Rerank retrieved documents using
    lexical overlap between the query
    and each document.

    Higher score = more relevant.
    """

    query_words = tokenize(query)

    reranked = []

    for document in documents:

        document_words = tokenize(
            document["content"]
        )

        if not query_words:
            lexical_score = 0.0

        else:

            overlap = (
                query_words
                & document_words
            )

            lexical_score = (
                len(overlap)
                / len(query_words)
            )

        # Convert Chroma distance into
        # a similarity-like score.
        semantic_score = 1 / (
            1 + document["distance"]
        )

        # Combine semantic and lexical scores.
        final_score = (
            0.6 * semantic_score
            + 0.4 * lexical_score
        )

        reranked.append(
            {
                **document,

                "lexical_score":
                lexical_score,

                "semantic_score":
                semantic_score,

                "rerank_score":
                final_score
            }
        )

    # Highest score first
    reranked.sort(
        key=lambda item:
        item["rerank_score"],
        reverse=True
    )

    return reranked

def get_unique_sources(
    retrieved_documents
):
    """
    Return unique knowledge-base sources
    while preserving retrieval order.
    """

    seen = set()

    unique_sources = []

    for document in retrieved_documents:

        source = document["source"]

        if source not in seen:

            seen.add(source)

            unique_sources.append(
                {
                    "source": source,

                    "distance":
                    document["distance"]
                }
            )

    return unique_sources


# ============================================================
# BUILD CONTEXT
# ============================================================

def build_context(
    query: str,
    top_k: int = 3
):

    results = retrieve_documents(
        query,
        top_k=top_k
    )

    context_parts = []

    for result in results:

        context_parts.append(

            f"Source: "
            f"{result['source']}\n"
            f"{result['content']}"

        )

    return "\n\n".join(
        context_parts
    )


# ============================================================
# ANALYZE TICKET USING RAG
# ============================================================

def analyze_ticket_with_rag(
    customer: str,
    issue: str
):

    """
    Retrieve, rerank and analyze
    the ticket using RAG.
    """

    # --------------------------------------------------------
    # STEP 1
    # Retrieve candidate documents
    # --------------------------------------------------------

    retrieved_documents = retrieve_documents(

        issue,

        top_k=5,

        distance_threshold=0.80

    )


    # --------------------------------------------------------
    # STEP 2
    # Rerank candidates
    # --------------------------------------------------------

    reranked_documents = rerank_documents(

        issue,

        retrieved_documents

    )


    # --------------------------------------------------------
    # STEP 3
    # Keep best results
    # --------------------------------------------------------

    final_documents = (
        reranked_documents[:3]
    )


    # --------------------------------------------------------
    # STEP 4
    # Build LLM context
    # --------------------------------------------------------

    context_parts = []

    for document in final_documents:

        context_parts.append(

            f"Source: "
            f"{document['source']}\n"
            f"{document['content']}"

        )

    context = "\n\n".join(
        context_parts
    )


    # --------------------------------------------------------
    # STEP 5
    # Analyze with LLM
    # --------------------------------------------------------

    analysis = analyze_ticket(

        customer=customer,

        issue=issue,

        context=context

    )


    # --------------------------------------------------------
    # STEP 6
    # Prepare sources
    # --------------------------------------------------------

    sources = []

    seen = set()

    for document in final_documents:

        source = document["source"]

        if source in seen:
            continue

        seen.add(source)

        sources.append(

            {
                "source":
                source,

                "distance":
                document["distance"],

                "rerank_score":
                document["rerank_score"]
            }

        )


    # --------------------------------------------------------
    # STEP 7
    # Return
    # --------------------------------------------------------

    return {

        "analysis":
        analysis,

        "sources":
        sources

    }
# ============================================================
# TEST RAG PIPELINE
# ============================================================

if __name__ == "__main__":

    index_documents()

    customer = "Microsoft"

    issue = (
        "Production API is returning "
        "500 errors after the latest deployment"
    )

    print(
        "\nAnalyzing ticket with RAG...\n"
    )

    result = analyze_ticket_with_rag(

        customer,

        issue

    )

    print(
        "AI ANALYSIS:"
    )

    print(
        "=================="
    )

    print(
        result["analysis"]
    )

    print(
        "\nKNOWLEDGE SOURCES:"
    )

    print(
        "=================="
    )

    for source in result["sources"]:

        print(
            f"Source: "
            f"{source['source']}"
        )

        print(
            f"Distance: "
            f"{source['distance']}"
        )

        print()