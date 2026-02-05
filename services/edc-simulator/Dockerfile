FROM python:3.11-slim
WORKDIR /app
COPY services/edc-simulator/requirements.txt services/edc-simulator/requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY services/edc-simulator/app ./app
COPY services/shared /app/services/shared
COPY services/__init__.py /app/services/__init__.py
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
