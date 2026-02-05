FROM python:3.11-slim
WORKDIR /app
COPY services/platform-core/requirements.txt services/platform-core/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY services/platform-core/app ./app
COPY services/shared /app/services/shared
COPY services/__init__.py /app/services/__init__.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007"]
