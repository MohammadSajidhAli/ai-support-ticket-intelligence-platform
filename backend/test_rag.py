from services.rag_service import (
    index_documents,
    retrieve_documents,
    rerank_documents
)


# ============================================================
# TEST CASES
# ============================================================

TEST_CASES = [

    {
        "name": "API Incident",

        "query":
        "Production API is returning 500 errors",

        "expected_sources": [
            "api_errors.txt"
        ]
    },

    {
        "name": "Authentication Issue",

        "query":
        "All users are unable to login because authentication tokens are failing",

        "expected_sources": [
            "authentication.txt"
        ]
    },

    {
        "name": "Database Issue",

        "query":
        "Production database connections are timing out",

        "expected_sources": [
            "database.txt"
        ]
    },

    {
        "name": "Deployment Issue",

        "query":
        "After today's deployment the health checks are failing",

        "expected_sources": [
            "deployment.txt"
        ]
    }

]


# ============================================================
# PRECISION@K
# ============================================================

def precision_at_k(
    retrieved_sources,
    expected_sources,
    k
):

    top_k = retrieved_sources[:k]

    if not top_k:
        return 0.0

    relevant = sum(
        1
        for source in top_k
        if source in expected_sources
    )

    return relevant / len(top_k)


# ============================================================
# RECALL@K
# ============================================================

def recall_at_k(
    retrieved_sources,
    expected_sources,
    k
):

    top_k = retrieved_sources[:k]

    if not expected_sources:
        return 0.0

    relevant = sum(
        1
        for source in expected_sources
        if source in top_k
    )

    return relevant / len(
        expected_sources
    )


# ============================================================
# RECIPROCAL RANK
# ============================================================

def reciprocal_rank(
    retrieved_sources,
    expected_sources
):

    for index, source in enumerate(
        retrieved_sources,
        start=1
    ):

        if source in expected_sources:

            return 1 / index

    return 0.0


# ============================================================
# RUN EVALUATION
# ============================================================

def run_evaluation():

    print("\n")

    print("=" * 70)

    print(
        "RERANKED RAG EVALUATION"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # Index
    # --------------------------------------------------------

    print(
        "\nIndexing knowledge base...\n"
    )

    index_documents()


    total_tests = len(
        TEST_CASES
    )

    total_precision_1 = 0.0

    total_precision_3 = 0.0

    total_recall_3 = 0.0

    total_mrr = 0.0


    # --------------------------------------------------------
    # Tests
    # --------------------------------------------------------

    for number, test in enumerate(
        TEST_CASES,
        start=1
    ):

        print("\n")

        print("-" * 70)

        print(
            f"TEST {number}: "
            f"{test['name']}"
        )

        print("-" * 70)


        print(
            f"\nQuery:\n"
            f"{test['query']}"
        )


        # ----------------------------------------------------
        # Retrieve more candidates
        # ----------------------------------------------------

        candidates = retrieve_documents(

            test["query"],

            top_k=5,

            distance_threshold=0.80

        )


        # ----------------------------------------------------
        # Rerank
        # ----------------------------------------------------

        results = rerank_documents(

            test["query"],

            candidates

        )


        retrieved_sources = []


        print(
            "\nReranked chunks:"
        )


        for rank, result in enumerate(
            results[:3],
            start=1
        ):

            source = result[
                "source"
            ]

            distance = result[
                "distance"
            ]

            rerank_score = result[
                "rerank_score"
            ]

            retrieved_sources.append(
                source
            )


            print(
                f"\nRank: {rank}"
            )

            print(
                f"Source: {source}"
            )

            print(
                f"Chroma distance: "
                f"{distance:.4f}"
            )

            print(
                f"Rerank score: "
                f"{rerank_score:.4f}"
            )

            print(
                "Content:"
            )

            print(
                result["content"][:200]
            )


        expected_sources = set(
            test["expected_sources"]
        )


        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        p1 = precision_at_k(

            retrieved_sources,

            expected_sources,

            1

        )


        p3 = precision_at_k(

            retrieved_sources,

            expected_sources,

            3

        )


        r3 = recall_at_k(

            retrieved_sources,

            expected_sources,

            3

        )


        mrr = reciprocal_rank(

            retrieved_sources,

            expected_sources

        )


        total_precision_1 += p1

        total_precision_3 += p3

        total_recall_3 += r3

        total_mrr += mrr


        print(
            "\nMetrics:"
        )

        print(
            f"Precision@1: "
            f"{p1:.2f}"
        )

        print(
            f"Precision@3: "
            f"{p3:.2f}"
        )

        print(
            f"Recall@3: "
            f"{r3:.2f}"
        )

        print(
            f"MRR: "
            f"{mrr:.2f}"
        )


    # ========================================================
    # FINAL RESULTS
    # ========================================================

    avg_precision_1 = (
        total_precision_1
        / total_tests
    )

    avg_precision_3 = (
        total_precision_3
        / total_tests
    )

    avg_recall_3 = (
        total_recall_3
        / total_tests
    )

    avg_mrr = (
        total_mrr
        / total_tests
    )


    print("\n")

    print("=" * 70)

    print(
        "FINAL RERANKED RAG EVALUATION"
    )

    print("=" * 70)


    print(
        f"\nTests: "
        f"{total_tests}"
    )

    print(
        f"Precision@1: "
        f"{avg_precision_1:.2f}"
    )

    print(
        f"Precision@3: "
        f"{avg_precision_3:.2f}"
    )

    print(
        f"Recall@3: "
        f"{avg_recall_3:.2f}"
    )

    print(
        f"MRR: "
        f"{avg_mrr:.2f}"
    )


    print("\n")


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    run_evaluation()