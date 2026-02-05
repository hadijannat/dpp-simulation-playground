# Simulation API

Export OpenAPI specs with:

```bash
make openapi
```

Primary flows:

- `POST /api/v1/sessions` create session
- `POST /api/v1/sessions/{id}/stories/{code}/start` start story
- `POST /api/v1/sessions/{id}/stories/{code}/steps/{idx}/execute` run step
- `POST /api/v1/sessions/{id}/stories/{code}/validate` validate story
