
# Deploying with FastAPI

**Note the .env file in there is on purpose and NONE of those keys work. They are there purely for demonstration purposes.**

## Installation and Running

1. Make sure you have FastAPI and uvicorn installed (it is in the requirements.txt)


### Running the App
1. From the `semantic-search-fastapi` directory, run `uvicorn api:app  --reload` to start your local flask app
2. Test the app by  going to [http://localhost:8000/docs](http://localhost:8000/docs)

### Using Docker

In the `deploy` directory:

to build: `docker build . --tag fastapi-demo:1`

You may need to run with a specified paltform if you use a macbook with the M1 chip like I do: 
`docker build . --tag fastapi-demo:1 --platform linux/amd64`

to run: `docker run -p 80:8000 --platform linux/amd64 fastapi-demo:1`

navigate to [http://localhost/docs](http://localhost/docs)

### To deploy docker image to Heroku
Docs [here](https://devcenter.heroku.com/articles/container-registry-and-runtime)

Tag image for Heroku: `docker tag fastapi-demo:1 registry.heroku.com/oreilly-sinan-mlops/web`

To push to Heroku: `docker push registry.heroku.com/oreilly-sinan-mlops/web`

To release new version: `heroku container:release web -a oreilly-sinan-mlops`

To see logs: `heroku logs -a oreilly-sinan-mlops -t`

Navigate to [https://oreilly-sinan-mlops.herokuapp.com/docs](https://oreilly-sinan-mlops.herokuapp.com/docs)


## Using the App

### API Endpoints

#### Document Ingest (POST `/document/ingest`)

Ingests a document into the system.

- **Request Payload**: JSON with the following properties:
  - `text` (required, string): The text of the document.
  - `chunking_strategy` (optional, string, default: "paragraph"): The strategy used to chunk the document.
  - `namespace` (optional, string, default: "default"): Namespace for categorizing the document.

- **Responses**:
  - `200 OK`: Returns the number of chunks created.
  - `422 Unprocessable Entity`: Validation errors.


#### Document Retrieve (POST `/document/retrieve`)

Retrieves documents based on a query.

- **Request Payload**: JSON with the following properties:
  - `query` (required, string): The query to match.
  - `re_ranking_strategy` (optional, string, default: "none"): Strategy to re-rank the retrieved documents.
  - `num_results` (optional, integer, default: 3): Number of results to return.
  - `namespace` (optional, string, default: "default"): Namespace where the document resides.

- **Responses**:
  - `200 OK`: Returns an array of matched documents.
  - `422 Unprocessable Entity`: Validation errors.

#### Conversation (POST `/conversation`)

Initiates or continues a conversation with the model.

- **Request Payload**: JSON with the following properties:
  - `message` (required, string): The message to send to the model.
  - `max_tokens`, `temperature`, `top_p`, `frequency_penalty`, `presence_penalty`, `stop`, `threshold` (optional): Parameters to fine-tune the model response.
  - `namespace` (optional, string, default: "default"): Namespace for categorizing the conversation.
  - `conversation_id` (optional, string): ID to maintain a continued conversation.

- **Responses**:
  - `200 OK`: Returns the model's text response and the conversation ID.
  - `422 Unprocessable Entity`: Validation errors.

For more details, go to the docs page of the local server: [http://localhost:8000/docs](http://localhost:8000/docs)


