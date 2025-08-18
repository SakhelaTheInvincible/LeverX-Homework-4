## Students & Rooms JSON REST API (Django + DRF)

Pragmatic REST API over existing JSON files in `input/rooms.json` and `input/students.json`.

- CRUD for students and rooms
- `__in` filtering on list endpoints
- List students by room
- Move student between rooms
- Swagger docs with examples (`/api/docs/`)

### Requirements

- Python 3.10+
- `uv` package manager (`pip install uv` or see `https://github.com/astral-sh/uv`)

### Setup

```bash
uv sync
```

Ensure `input/rooms.json` and `input/students.json` exist.
```

### Run

```bash
uv run python manage.py runserver 0.0.0.0:8000
```

Open Swagger UI: `http://localhost:8000/api/docs/`

### Endpoints (summary)

- `GET /api/rooms/` — list rooms, supports `ids__in=1,2`
- `POST /api/rooms/` — create room `{ name }`
- `GET /api/rooms/{room_id}/` — get room
- `PUT /api/rooms/{room_id}/` — update room `{ name }`
- `DELETE /api/rooms/{room_id}/` — delete room

- `GET /api/students/` — list students, supports `ids__in=1,2` and `room__in=1,2`
- `POST /api/students/` — create student `{ name, room }`
- `GET /api/students/{student_id}/` — get student
- `PUT /api/students/{student_id}/` — update student `{ name, room }`
- `DELETE /api/students/{student_id}/` — delete student

- `GET /api/rooms/{room_id}/students/` — list students in room
- `POST /api/students/{student_id}/move/` — move student `{ to_room_id }`

- `GET /api/combined/` — rooms with embedded students (via provided `DataCombiner`)

### Error format

```json
{
  "code": "validation_error",
  "message": "Invalid student data",
  "details": {"name": ["This field is required."]}
}
```

Possible codes: `validation_error`, `not_found`, `room_not_found`.

### Design notes (SOLID)

- Single Responsibility: repositories only handle JSON persistence; views orchestrate; serializers validate.
- Open/Closed: new storage can implement the repository interfaces without touching views.
- Liskov: JSON repos conform to room/student repository contracts.
- Interface Segregation: separate `RoomsRepository` and `StudentsRepository`.
- Dependency Inversion: views depend on abstractions, wired with JSON implementations.

## Students & Rooms API (FastAPI) — JSON storage

Pragmatic REST API to manage students and rooms stored in JSON files. Implements SOLID via layered design: models, repositories, services, routers.

### UV setup

- Install `uv` per docs (`pipx install uv`).
- From project root (`LeverX-Homework-4`):

```bash
uv sync
uv run serve
```

Environment vars:

- `DATA_DIR` (optional): directory holding `students.json` and `rooms.json`. Defaults to `./input`.
- `PORT` (optional): server port. Defaults to 8000.

### Run

```bash
uv run serve
```

Open API docs: `http://localhost:8000/docs`

Export OpenAPI spec:

```bash
uv run export-openapi
```

### File layout

- `app/models.py` — Pydantic schemas and error model
- `app/storage.py` — JSON loader, combiner, and JSON repository (low-level IO)
- `app/repositories.py` — repository interfaces and JSON implementations
- `app/services.py` — business logic (ID allocation, validations, move operation)
- `app/routers.py` — FastAPI endpoints
- `app/main.py` — app factory and server entrypoint
- `input/rooms.json`, `input/students.json` — data files

### Data format

- Student: `{ "id": int, "name": str, "room": int|null }`
- Room: `{ "id": int, "name": str }`

### Error format

All errors use:

```json
{ "code": "STRING_CODE", "message": "Human readable", "details": {"optional": "info"} }
```

Possible codes: `STUDENT_NOT_FOUND`, `ROOM_NOT_FOUND`.

### Endpoints (summary)

- `GET /students?skip&limit` — list students
- `GET /students/{id}` — get student
- `POST /students` — create
- `PATCH /students/{id}` — update
- `DELETE /students/{id}` — delete
- `POST /students/{id}/move` — move to another room
- `GET /rooms?skip&limit` — list rooms
- `GET /rooms/{id}` — get room
- `POST /rooms` — create
- `PATCH /rooms/{id}` — update
- `DELETE /rooms/{id}` — delete
- `GET /rooms/{id}/students` — list students for room

OpenAPI includes request/response models and sample schemas; see `/docs` or `openapi.json`.

### SOLID mapping

- Single Responsibility: routers (transport), services (business), repositories (persistence), storage (IO), models (schemas).
- Open/Closed: easy to introduce a different repository (e.g., DB) via interfaces.
- Liskov: interfaces ensure substitutability of repositories.
- Interface Segregation: separate `StudentRepository` and `RoomRepository`.
- Dependency Inversion: services depend on abstractions; concrete JSON impls wired in `main`.



