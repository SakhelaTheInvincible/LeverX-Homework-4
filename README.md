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
uv run python manage.py runserver
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

Possible codes: `validation_error`, `not_found`, `room_not_found` and more.

### Examples (success & errors)

- Provided example responses for successful requests which are covered across Swagger for each operation.
- Each of them additionally have defined real-case scenario errors and examples

Success example (GET `/api/students/?room__in=473`):
```json
[
  {
    "birthday": "2011-08-22T00:00:00.000000",
    "id": 0,
    "name": "Peggy Ryan",
    "room": 473,
    "sex": "M"
  }
]
```

Error example (GET `/api/students/?ids__in=1,x,3`):
```json
{
  "code": "validation_error",
  "message": "Invalid query parameter",
  "details": {"ids__in": ["Expected comma-separated integers."]}
}
```