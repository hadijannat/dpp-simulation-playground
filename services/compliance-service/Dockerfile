FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY rules ./rules
ENV RULES_DIR=/app/rules
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
