FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .

ENV CHROMA_DIR=/data/chroma_store
ENV UPLOAD_DIR=/data/uploads

EXPOSE 8000

CMD ["uvicorn", "paperpilot.api:app", "--host", "0.0.0.0", "--port", "8000"]
