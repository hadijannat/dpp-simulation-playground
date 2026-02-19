FROM python:3.11-slim
WORKDIR /app
COPY services/compliance-service/requirements.txt services/compliance-service/requirements-dev.txt ./
COPY requirements/constraints.txt /constraints.txt
RUN pip install --no-cache-dir -c /constraints.txt -r requirements.txt
COPY services/compliance-service/app ./app
COPY services/shared /app/services/shared
COPY services/__init__.py /app/services/__init__.py
COPY services/compliance-service/rules ./rules
ENV RULES_DIR=/app/rules
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
