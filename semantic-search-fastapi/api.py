import hashlib
import os
import re
from datetime import datetime

import openai
import pinecone
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from openai.embeddings_utils import get_embeddings
from pydantic import BaseModel

from chunking_utils import overlapping_chunks
# optional use of supabase for conversation history
from conversation_utils import ChatbotGPT
from retrieval_utils import get_results

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")
pinecone_key = os.getenv("PINECONE_API_KEY")

app = FastAPI()

INDEX_NAME = 'semantic-search'
ENGINE = 'text-embedding-ada-002'

if pinecone_key:
    pinecone.init(api_key=pinecone_key, environment="us-west1-gcp")

    if not INDEX_NAME in pinecone.list_indexes():
        pinecone.create_index(
            INDEX_NAME,  # The name of the index to create.
            dimension=1536,  # The dimensionality of the vectors that will be indexed.
            metric='cosine',  # The similarity metric to use when searching the index.
            pod_type="p1"  # The type of Pinecone pod to use for hosting the index (in this case, a p1 pod).
        )
        print('Pinecone index created')
    else:
        print('Pinecone index already exists')

    # Store the index as a variable
    index = pinecone.Index(INDEX_NAME)


def my_hash(s):
    # Return the MD5 hash of the input string as a hexadecimal string
    return hashlib.md5(s.encode()).hexdigest()


class DocumentInputRequest(BaseModel):
    text: str
    chunking_strategy: str = "paragraph"
    namespace: str = "default"


class DocumentInputResponse(BaseModel):
    chunks_count: int


class DocumentRetrieveRequest(BaseModel):
    query: str
    re_ranking_strategy: str = "none"
    num_results: int = 3
    namespace: str = "default"


class DocumentResponse(BaseModel):
    text: str
    date_uploaded: datetime
    score: float
    id: str


class DocumentRetrieveResponse(BaseModel):
    documents: list


class ConversationRequest(BaseModel):
    message: str
    max_tokens: int = 100
    temperature: float = 0.9
    top_p: float = 1
    frequency_penalty: float = 0
    presence_penalty: float = 0
    stop: list = None
    threshold: float = 0.9
    namespace: str = "default"
    conversation_id: str = None


class ConversationResponse(BaseModel):
    text: str
    conversation_id: str


@app.post("/document/ingest", response_model=DocumentInputResponse)
async def document_ingest(request: DocumentInputRequest):
    if not pinecone_key:
        return DocumentInputResponse(chunks_count=0)
    text = request.text
    chunking_strategy = request.chunking_strategy
    if chunking_strategy == "sentence":
        chunks = re.split(r' *[\.\?!][\'"\)\]]* *', text)
    elif chunking_strategy == "paragraph":
        chunks = text.split('\n')
    elif chunking_strategy == "none":
        chunks = [text]
    elif 'overlapping' in chunking_strategy:
        _, max_tokens, overlapping_factor = chunking_strategy.split('-')
        chunks = overlapping_chunks(text, max_tokens=500, overlapping_factor=5)
    else:
        raise Exception("Invalid chunking strategy")

    chunks = [c.strip() for c in chunks if len(c.strip()) > 0]
    print(chunks)

    embeddings = get_embeddings(chunks, engine=ENGINE)

    pinecone_request = [
        (
            my_hash(text),  # A unique ID for each string, generated using the my_hash() function
            embedding,  # The vector embedding of the string
            dict(text=text, date_uploaded=datetime.utcnow())
            # A dictionary of metadata, including the original text and the current UTC date and time
        )
        for text, embedding in zip(chunks, embeddings)
        # Iterate over each input string and its corresponding vector embedding
    ]

    upserted_count = index.upsert(pinecone_request, namespace=request.namespace).get('upserted_count')

    return DocumentInputResponse(chunks_count=upserted_count)


@app.post("/document/retrieve", response_model=DocumentRetrieveResponse)
async def document_retrieve(request: DocumentRetrieveRequest):
    if not pinecone_key:
        return DocumentRetrieveResponse(documents=[])
    query = request.query
    re_ranking_strategy = request.re_ranking_strategy
    namespace = request.namespace
    num_results = request.num_results
    results = get_results(index, query, re_ranking_strategy, num_results, namespace, ENGINE)

    results = [
        DocumentResponse(
            text=r['metadata']['text'],
            date_uploaded=r['metadata']['date_uploaded'],
            score=r['score'],
            id=r['id']
        ) for r in results
    ]
    return DocumentRetrieveResponse(documents=results)


@app.post("/conversation", response_model=ConversationResponse)
async def conversation(request: ConversationRequest):
    message = request.message
    namespace = request.namespace
    max_tokens = request.max_tokens
    temperature = request.temperature
    top_p = request.top_p
    frequency_penalty = request.frequency_penalty
    presence_penalty = request.presence_penalty
    stop = request.stop
    threshold = request.threshold

    conversation_id = request.conversation_id
    c = ChatbotGPT(namespace, index, ENGINE, threshold=threshold, conversation_id=conversation_id)
    response = c.user_turn(message)
    print(response)

    return ConversationResponse(text=response['content'], conversation_id=c.conversation_id)


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
