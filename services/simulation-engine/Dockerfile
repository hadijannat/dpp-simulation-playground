FROM python:3.11-slim
WORKDIR /app
COPY services/simulation-engine/requirements.txt services/simulation-engine/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY services/simulation-engine/app ./app
COPY services/simulation-engine/alembic.ini ./alembic.ini
COPY services/simulation-engine/alembic ./alembic
COPY services/simulation-engine/data ./data
COPY services/shared /app/services/shared
COPY services/__init__.py /app/services/__init__.py
ENV STORY_DATA_DIR=/app/data/stories
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
