from __future__ import annotations

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample

from .repositories import (
    JsonRoomsRepository,
    JsonStudentsRepository,
    DataCombiner,
    JsonDataLoader,
)
from .serializers import (
    RoomSerializer,
    StudentSerializer,
    MoveStudentSerializer,
    ErrorResponseSerializer,
    CombinedRoomSerializer,
)


rooms_repo = JsonRoomsRepository()
students_repo = JsonStudentsRepository()


def not_found(detail: str) -> Response:
    return Response({"code": "not_found", "message": detail}, status=status.HTTP_404_NOT_FOUND)


def parse_comma_separated_integers(raw_value: str, parameter_name: str) -> tuple[list[int] | None, Response | None]:
    try:
        values = [int(x) for x in raw_value.split(",") if x.strip()]
        return values, None
    except ValueError:
        return None, Response(
            {
                "code": "validation_error",
                "message": "Invalid query parameter",
                "details": {parameter_name: ["Expected comma-separated integers."]},
            },
            status=400,
        )


class RoomViewSet(ViewSet):
    """Rooms endpoint group"""

    @extend_schema(
        tags=["rooms"],
        summary="List rooms",
        description="Return all rooms. Use the optional filter `ids__in` to return only specific room ids.",
        parameters=[
            OpenApiParameter(name="ids__in", description="Comma-separated room ids to filter", required=False, type=str),
        ],
        responses={200: RoomSerializer(many=True), 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "List rooms response",
                response_only=True,
                value=[{"id": 0,"name": "Room #0"}, {"id": 1,"name": "Room #1"}],
            ),
            OpenApiExample(
                "Invalid ids__in format",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid query parameter",
                    "details": {"ids__in": ["Expected comma-separated integers."]},
                },
            ),
        ],
    )
    def list(self, request: Request) -> Response:
        ids_in_param = request.query_params.get("ids__in")
        rooms = rooms_repo.list()
        if ids_in_param:
            ids_list, error = parse_comma_separated_integers(ids_in_param, "ids__in")
            if error is not None:
                return error
            ids_set = set(ids_list or [])
            rooms = [r for r in rooms if r.id in ids_set]
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=["rooms"],
        summary="Create room",
        description="Create a new room with a name.",
        request=RoomSerializer,
        responses={201: RoomSerializer, 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample("Create room request", request_only=True, value={"name": "Physics"}),
            OpenApiExample("Create room response", response_only=True, value={"id": 10, "name": "Physics"}),
            OpenApiExample(
                "Create room validation error",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid room data",
                    "details": {"name": ["This field is required."]},
                },
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        serializer = RoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid room data", "details": serializer.errors}, status=400)
        created = rooms_repo.create(name=serializer.validated_data["name"])
        return Response(RoomSerializer(created).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["rooms"],
        summary="Get room",
        description="Retrieve a single room by id.",
        responses={200: RoomSerializer, 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Room not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Room not found"},
            )
        ],
    )
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        room = rooms_repo.get(room_id)
        if not room:
            return not_found("Room not found")
        return Response(RoomSerializer(room).data)

    @extend_schema(
        tags=["rooms"],
        summary="Update room",
        description="Replace a room's attributes.",
        request=RoomSerializer,
        responses={200: RoomSerializer, 404: ErrorResponseSerializer, 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Update room validation error",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid room data",
                    "details": {"name": ["This field may not be blank."]},
                },
            ),
            OpenApiExample(
                "Update room not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Room not found"},
            ),
        ],
    )
    def update(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        serializer = RoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid room data", "details": serializer.errors}, status=400)
        updated = rooms_repo.update(room_id, name=serializer.validated_data["name"])
        if not updated:
            return not_found("Room not found")
        return Response(RoomSerializer(updated).data)

    @extend_schema(
        tags=["rooms"],
        summary="Delete room",
        description="Delete a room by id.",
        responses={204: None, 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Delete room not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Room not found"},
            )
        ],
    )
    def destroy(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        deleted = rooms_repo.delete(room_id)
        if not deleted:
            return not_found("Room not found")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["rooms"],
        summary="List students in a room",
        description="Return all students that belong to the given room id.",
        responses={200: StudentSerializer(many=True), 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Students in room response",
                response_only=True,
                value=[
                    {
                        "birthday": "2011-08-22T00:00:00.000000",
                        "id": 0,
                        "name": "Peggy Ryan",
                        "room": 473,
                        "sex": "M"
                    }
                ],
            ),
            OpenApiExample(
                "Room not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Room not found"},
            ),
        ],
    )
    @action(detail=True, methods=["get"], url_path="students")
    def students(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        if not rooms_repo.get(room_id):
            return not_found("Room not found")
        students = students_repo.list(room_in=[room_id])
        return Response(StudentSerializer(students, many=True).data)


class StudentViewSet(ViewSet):
    """Students endpoint group"""

    @extend_schema(
        tags=["students"],
        summary="List students",
        description="Return all students. Use `ids__in` and/or `room__in` to filter.",
        parameters=[
            OpenApiParameter(name="ids__in", description="Comma-separated student ids", required=False, type=str),
            OpenApiParameter(name="room__in", description="Comma-separated room ids", required=False, type=str),
        ],
        responses={200: StudentSerializer(many=True), 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "List students response",
                response_only=True,
                value=[
                    {
                        "birthday": "2011-08-22T00:00:00.000000",
                        "id": 0,
                        "name": "Peggy Ryan",
                        "room": 473,
                        "sex": "M"
                    }
                ],
            ),
            OpenApiExample(
                "Invalid ids__in format",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid query parameter",
                    "details": {"ids__in": ["Expected comma-separated integers."]},
                },
            ),
            OpenApiExample(
                "Invalid room__in format",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid query parameter",
                    "details": {"room__in": ["Expected comma-separated integers."]},
                },
            ),
        ],
    )
    def list(self, request: Request) -> Response:
        ids_in = request.query_params.get("ids__in")
        room_in = request.query_params.get("room__in")
        ids = None
        rooms = None
        if ids_in:
            ids, error = parse_comma_separated_integers(ids_in, "ids__in")
            if error is not None:
                return error
        if room_in:
            rooms, error = parse_comma_separated_integers(room_in, "room__in")
            if error is not None:
                return error
        students = students_repo.list(ids_in=ids, room_in=rooms)
        return Response(StudentSerializer(students, many=True).data)

    @extend_schema(
        tags=["students"],
        summary="Create student",
        description="Create a new student. The target room must exist.",
        request=StudentSerializer,
        responses={201: StudentSerializer, 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Create student request",
                request_only=True,
                value={
                    "birthday": "2011-08-22T00:00:00.000000",
                    "id": 0,
                    "name": "Peggy Ryan",
                    "room": 473,
                    "sex": "M"
                },
            ),
            OpenApiExample(
                "Create student response",
                response_only=True,
                value={
                    "birthday": "2011-08-22T00:00:00.000000",
                    "id": 0,
                    "name": "Peggy Ryan",
                    "room": 473,
                    "sex": "M"
                },
            ),
            OpenApiExample(
                "Create student validation error",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid student data",
                    "details": {
                        "name": ["This field is required."],
                        "room": ["A valid integer is required."],
                        "sex": ["X is not a valid choice."],
                        "birthday": ["Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDTHH:MM:SS.ffffff."],
                    },
                },
            ),
            OpenApiExample(
                "Create student room not found",
                response_only=True,
                status_codes=["400"],
                value={"code": "room_not_found", "message": "Target room does not exist"},
            ),
        ],
    )
    def create(self, request: Request) -> Response:
        serializer = StudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid student data", "details": serializer.errors}, status=400)
        if not rooms_repo.get(serializer.validated_data["room"]):
            return Response({"code": "room_not_found", "message": "Target room does not exist"}, status=400)
        created = students_repo.create(**serializer.validated_data)
        return Response(StudentSerializer(created).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=["students"],
        summary="Get student",
        description="Retrieve a single student by id.",
        responses={200: StudentSerializer, 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Student not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Student not found"},
            )
        ],
    )
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        student = students_repo.get(student_id)
        if not student:
            return not_found("Student not found")
        return Response(StudentSerializer(student).data)

    @extend_schema(
        tags=["students"],
        summary="Update student",
        description="Replace a student's attributes. The target room must exist.",
        request=StudentSerializer,
        responses={200: StudentSerializer, 404: ErrorResponseSerializer, 400: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Update student request",
                request_only=True,
                value={
                    "birthday": "2011-08-22T00:00:00.000000",
                    "name": "Peggy Ryan",
                    "room": 473,
                    "sex": "M"
                },
            ),
            OpenApiExample(
                "Update student validation error",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid student data",
                    "details": {
                        "room": ["A valid integer is required."],
                        "sex": ["X is not a valid choice."],
                        "birthday": ["Datetime has wrong format. Use one of these formats instead: YYYY-MM-DDTHH:MM:SS.ffffff."],
                    },
                },
            ),
            OpenApiExample(
                "Update student not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Student not found"},
            ),
            OpenApiExample(
                "Update student room not found",
                response_only=True,
                status_codes=["400"],
                value={"code": "room_not_found", "message": "Target room does not exist"},
            ),
        ],
    )
    def update(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        serializer = StudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid student data", "details": serializer.errors}, status=400)
        if not rooms_repo.get(serializer.validated_data["room"]):
            return Response({"code": "room_not_found", "message": "Target room does not exist"}, status=400)
        updated = students_repo.update(student_id, **serializer.validated_data)
        if not updated:
            return not_found("Student not found")
        return Response(StudentSerializer(updated).data)

    @extend_schema(
        tags=["students"],
        summary="Delete student",
        description="Delete a student by id.",
        responses={204: None, 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample(
                "Delete student not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Student not found"},
            )
        ],
    )
    def destroy(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        deleted = students_repo.delete(student_id)
        if not deleted:
            return not_found("Student not found")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["students"],
        summary="Move student to another room",
        description="Change the student's room to the target room id.",
        request=MoveStudentSerializer,
        responses={200: StudentSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer},
        examples=[
            OpenApiExample("Move request", request_only=True, value={"to_room_id": 2}),
            OpenApiExample(
                "Move response",
                response_only=True,
                value={
                    "birthday": "2011-08-22T00:00:00.000000",
                    "id": 0,
                    "name": "Peggy Ryan",
                    "room": 473,
                    "sex": "M"
                },
            ),
            OpenApiExample(
                "Move validation error",
                response_only=True,
                status_codes=["400"],
                value={
                    "code": "validation_error",
                    "message": "Invalid move payload",
                    "details": {"to_room_id": ["This field is required."]},
                },
            ),
            OpenApiExample(
                "Move target room not found",
                response_only=True,
                status_codes=["400"],
                value={"code": "room_not_found", "message": "Target room does not exist"},
            ),
            OpenApiExample(
                "Move student not found",
                response_only=True,
                status_codes=["404"],
                value={"code": "not_found", "message": "Student not found"},
            ),
        ],
    )
    @action(detail=True, methods=["post"], url_path="move")
    def move(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        student = students_repo.get(student_id)
        if not student:
            return not_found("Student not found")
        serializer = MoveStudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid move payload", "details": serializer.errors}, status=400)
        to_room_id = serializer.validated_data["to_room_id"]
        if not rooms_repo.get(to_room_id):
            return Response({"code": "room_not_found", "message": "Target room does not exist"}, status=400)
        moved = students_repo.move(student_id, to_room_id)
        return Response(StudentSerializer(moved).data)


class CombinedViewSet(ViewSet):
    """combined endpoint group"""

    @extend_schema(
        tags=["student_room"],
        summary="Combined rooms with students",
        description="Return rooms with embedded students arrays.",
        responses={200: CombinedRoomSerializer(many=True)},
        examples=[
            OpenApiExample(
                "Combined response",
                response_only=True,
                value=[{
                        "id": 0,
                        "name": "Room #0",
                        "students": [
                            {
                                "id": 106,
                                "name": "Craig Riggs"
                            },
                            {
                                "id": 1924,
                                "name": "Rodney Hart"
                            },
                            {
                                "id": 2179,
                                "name": "Henry Anderson"
                            },
                            {
                                "id": 2217,
                                "name": "Tanner Buck"
                            },
                        ]
                    }
                ],
            )
        ],
    )
    def list(self, request: Request) -> Response:
        rooms = JsonDataLoader().load(settings.JSON_ROOMS_PATH)
        students = JsonDataLoader().load(settings.JSON_STUDENTS_PATH)
        combined = DataCombiner(rooms, students).combine()
        return Response(combined)


