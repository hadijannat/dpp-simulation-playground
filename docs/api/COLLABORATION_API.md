# Collaboration Service API

Base path: `/api/v1`

## Endpoints

### Annotations
- `GET /annotations`
- `POST /annotations`
- `GET /annotations/{annotation_id}`

### Gap Reports
- `GET /gap_reports`
- `POST /gap_reports`
- `GET /gap_reports/{gap_id}`

### Votes
- `POST /votes`

### Comments
- `GET /comments`
- `POST /comments`

## Auth
All endpoints require JWT with roles: `developer`, `manufacturer`, `admin`, or `regulator` (see service RBAC rules).
