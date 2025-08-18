from __future__ import annotations

from typing import Any, Dict, List

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
)


rooms_repo = JsonRoomsRepository()
students_repo = JsonStudentsRepository()


def not_found(detail: str) -> Response:
    return Response({"code": "not_found", "message": detail}, status=status.HTTP_404_NOT_FOUND)


class RoomViewSet(ViewSet):
    """Rooms endpoint group"""

    @extend_schema(
        tags=["rooms"],
        parameters=[
            OpenApiParameter(name="ids__in", description="Comma-separated room ids to filter", required=False, type=str),
        ],
        responses={200: RoomSerializer(many=True)},
        examples=[
            OpenApiExample(
                "List rooms",
                response_only=True,
                value=[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}],
            )
        ],
    )
    def list(self, request: Request) -> Response:
        ids_in_param = request.query_params.get("ids__in")
        rooms = rooms_repo.list()
        if ids_in_param:
            ids = {int(x) for x in ids_in_param.split(",") if x.strip()}
            rooms = [r for r in rooms if r.id in ids]
        serializer = RoomSerializer(rooms, many=True)
        return Response(serializer.data)

    @extend_schema(tags=["rooms"], request=RoomSerializer, responses={201: RoomSerializer, 400: ErrorResponseSerializer}, examples=[
        OpenApiExample("Create room", request_only=True, value={"name": "Physics"})
    ])
    def create(self, request: Request) -> Response:
        serializer = RoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid room data", "details": serializer.errors}, status=400)
        created = rooms_repo.create(name=serializer.validated_data["name"])
        return Response(RoomSerializer(created).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["rooms"], responses={200: RoomSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        room = rooms_repo.get(room_id)
        if not room:
            return not_found("Room not found")
        return Response(RoomSerializer(room).data)

    @extend_schema(tags=["rooms"], request=RoomSerializer, responses={200: RoomSerializer, 404: ErrorResponseSerializer, 400: ErrorResponseSerializer})
    def update(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        serializer = RoomSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid room data", "details": serializer.errors}, status=400)
        updated = rooms_repo.update(room_id, name=serializer.validated_data["name"])
        if not updated:
            return not_found("Room not found")
        return Response(RoomSerializer(updated).data)

    @extend_schema(tags=["rooms"], responses={204: None, 404: ErrorResponseSerializer})
    def destroy(self, request: Request, pk: str | None = None) -> Response:
        room_id = int(pk) if pk is not None else 0
        deleted = rooms_repo.delete(room_id)
        if not deleted:
            return not_found("Room not found")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(tags=["rooms"], responses={200: StudentSerializer(many=True), 404: ErrorResponseSerializer})
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
        parameters=[
            OpenApiParameter(name="ids__in", description="Comma-separated student ids", required=False, type=str),
            OpenApiParameter(name="room__in", description="Comma-separated room ids", required=False, type=str),
        ],
        responses={200: StudentSerializer(many=True)},
    )
    def list(self, request: Request) -> Response:
        ids_in = request.query_params.get("ids__in")
        room_in = request.query_params.get("room__in")
        ids = [int(x) for x in ids_in.split(",") if x.strip()] if ids_in else None
        rooms = [int(x) for x in room_in.split(",") if x.strip()] if room_in else None
        students = students_repo.list(ids_in=ids, room_in=rooms)
        return Response(StudentSerializer(students, many=True).data)

    @extend_schema(tags=["students"], request=StudentSerializer, responses={201: StudentSerializer, 400: ErrorResponseSerializer})
    def create(self, request: Request) -> Response:
        serializer = StudentSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"code": "validation_error", "message": "Invalid student data", "details": serializer.errors}, status=400)
        if not rooms_repo.get(serializer.validated_data["room"]):
            return Response({"code": "room_not_found", "message": "Target room does not exist"}, status=400)
        created = students_repo.create(**serializer.validated_data)
        return Response(StudentSerializer(created).data, status=status.HTTP_201_CREATED)

    @extend_schema(tags=["students"], responses={200: StudentSerializer, 404: ErrorResponseSerializer})
    def retrieve(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        student = students_repo.get(student_id)
        if not student:
            return not_found("Student not found")
        return Response(StudentSerializer(student).data)

    @extend_schema(tags=["students"], request=StudentSerializer, responses={200: StudentSerializer, 404: ErrorResponseSerializer, 400: ErrorResponseSerializer})
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

    @extend_schema(tags=["students"], responses={204: None, 404: ErrorResponseSerializer})
    def destroy(self, request: Request, pk: str | None = None) -> Response:
        student_id = int(pk) if pk is not None else 0
        deleted = students_repo.delete(student_id)
        if not deleted:
            return not_found("Student not found")
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(tags=["students"], request=MoveStudentSerializer, responses={200: StudentSerializer, 400: ErrorResponseSerializer, 404: ErrorResponseSerializer}, examples=[
        OpenApiExample("Move request", request_only=True, value={"to_room_id": 2}),
        OpenApiExample("Move response", response_only=True, value={"id": 5, "name": "Alice", "room": 2}),
    ])
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
    """Helpers endpoint group (combined view)"""

    @extend_schema(tags=["helpers"], responses={200: None}, description="Combined rooms with students using provided combiner")
    def list(self, request: Request) -> Response:
        rooms = JsonDataLoader().load(settings.JSON_ROOMS_PATH)
        students = JsonDataLoader().load(settings.JSON_STUDENTS_PATH)
        combined = DataCombiner(rooms, students).combine()
        return Response(combined)


