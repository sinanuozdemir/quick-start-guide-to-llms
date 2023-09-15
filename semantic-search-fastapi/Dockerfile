FROM python:3.9

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/

ENV PORT=8000

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT}
