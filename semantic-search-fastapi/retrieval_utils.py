from openai.embeddings_utils import get_embeddings


def get_results(index, query, re_ranking_strategy, num_results, namespace, engine):
    print(f"Query: {query} - Re-ranking strategy: {re_ranking_strategy} - Num results: {num_results}")

    query_embedding = get_embeddings([query], engine=engine)[0]

    top_results = index.query(
        vector=query_embedding,
        top_k=num_results,
        namespace=namespace,
        include_metadata=True  # gets the metadata (dates, text, etc)
    ).get('matches')

    if re_ranking_strategy == "none":
        results = top_results
    elif re_ranking_strategy == "date":
        results = sorted(top_results, key=lambda x: x['metadata']['date_uploaded'], reverse=True)
    elif re_ranking_strategy == "cross_encoder":
        # if you want to include cross_encoder, put it here!
        results = top_results
    else:
        raise Exception("Invalid re-ranking strategy")
    return results
