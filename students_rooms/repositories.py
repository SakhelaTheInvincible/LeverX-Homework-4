from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from django.conf import settings


# SOLID: Define repository interfaces and JSON-backed implementations


class RepositoryError(Exception):
    pass


@dataclass
class Room:
    id: int
    name: str


@dataclass
class Student:
    id: int
    name: str
    room: int


class RoomsRepository:
    def list(self) -> List[Room]:
        raise NotImplementedError

    def get(self, room_id: int) -> Optional[Room]:
        raise NotImplementedError

    def create(self, name: str) -> Room:
        raise NotImplementedError

    def update(self, room_id: int, name: str) -> Optional[Room]:
        raise NotImplementedError

    def delete(self, room_id: int) -> bool:
        raise NotImplementedError


class StudentsRepository:
    def list(self, *, ids_in: Optional[Iterable[int]] = None, room_in: Optional[Iterable[int]] = None) -> List[Student]:
        raise NotImplementedError

    def get(self, student_id: int) -> Optional[Student]:
        raise NotImplementedError

    def create(self, name: str, room: int) -> Student:
        raise NotImplementedError

    def update(self, student_id: int, name: Optional[str] = None, room: Optional[int] = None) -> Optional[Student]:
        raise NotImplementedError

    def delete(self, student_id: int) -> bool:
        raise NotImplementedError

    def move(self, student_id: int, to_room_id: int) -> Optional[Student]:
        raise NotImplementedError


class JsonFileRepositoryMixin:
    file_path: str

    def _read(self) -> List[Dict[str, Any]]:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as exc:
            raise RepositoryError(f"Invalid JSON in {self.file_path}") from exc

    def _write(self, items: List[Dict[str, Any]]) -> None:
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(items, f, ensure_ascii=False, indent=2)


class JsonRoomsRepository(JsonFileRepositoryMixin, RoomsRepository):
    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path or settings.JSON_ROOMS_PATH

    def list(self) -> List[Room]:
        rooms_raw = self._read()
        normalized: List[Room] = []
        for r in rooms_raw:
            normalized.append(Room(id=int(r.get("id")), name=str(r.get("name"))))
        return normalized

    def get(self, room_id: int) -> Optional[Room]:
        for r in self._read():
            if int(r.get("id")) == int(room_id):
                return Room(id=int(r.get("id")), name=str(r.get("name")))
        return None

    def _next_id(self, rooms: List[Dict[str, Any]]) -> int:
        return (max((r["id"] for r in rooms), default=0) + 1)

    def create(self, name: str) -> Room:
        rooms = self._read()
        room = {"id": self._next_id(rooms), "name": name}
        rooms.append(room)
        self._write(rooms)
        return Room(id=int(room["id"]), name=str(room["name"]))

    def update(self, room_id: int, name: str) -> Optional[Room]:
        rooms = self._read()
        for r in rooms:
            if r.get("id") == room_id:
                r["name"] = name
                self._write(rooms)
                return Room(id=int(r["id"]), name=str(r["name"]))
        return None

    def delete(self, room_id: int) -> bool:
        rooms = self._read()
        new_rooms = [r for r in rooms if r.get("id") != room_id]
        if len(new_rooms) == len(rooms):
            return False
        self._write(new_rooms)
        return True


class JsonStudentsRepository(JsonFileRepositoryMixin, StudentsRepository):
    def __init__(self, file_path: Optional[str] = None) -> None:
        self.file_path = file_path or settings.JSON_STUDENTS_PATH

    def list(self, *, ids_in: Optional[Iterable[int]] = None, room_in: Optional[Iterable[int]] = None) -> List[Student]:
        items = self._read()
        if ids_in is not None:
            ids_set = set(int(i) for i in ids_in)
            items = [s for s in items if int(s.get("id")) in ids_set]
        if room_in is not None:
            room_set = set(int(r) for r in room_in)
            items = [s for s in items if int(s.get("room")) in room_set]
        normalized: List[Student] = []
        for s in items:
            normalized.append(
                Student(
                    id=int(s.get("id")),
                    name=str(s.get("name")),
                    room=int(s.get("room")),
                )
            )
        return normalized

    def get(self, student_id: int) -> Optional[Student]:
        for s in self._read():
            if int(s.get("id")) == int(student_id):
                return Student(id=int(s.get("id")), name=str(s.get("name")), room=int(s.get("room")))
        return None

    def _next_id(self, students: List[Dict[str, Any]]) -> int:
        return (max((s["id"] for s in students), default=0) + 1)

    def create(self, name: str, room: int) -> Student:
        students = self._read()
        student = {"id": self._next_id(students), "name": name, "room": room}
        students.append(student)
        self._write(students)
        return Student(id=int(student["id"]), name=str(student["name"]), room=int(student["room"]))

    def update(self, student_id: int, name: Optional[str] = None, room: Optional[int] = None) -> Optional[Student]:
        students = self._read()
        for s in students:
            if s.get("id") == student_id:
                if name is not None:
                    s["name"] = name
                if room is not None:
                    s["room"] = room
                self._write(students)
                return Student(id=int(s["id"]), name=str(s["name"]), room=int(s.get("room")))
        return None

    def delete(self, student_id: int) -> bool:
        students = self._read()
        new_students = [s for s in students if s.get("id") != student_id]
        if len(new_students) == len(students):
            return False
        self._write(new_students)
        return True

    def move(self, student_id: int, to_room_id: int) -> Optional[Student]:
        return self.update(student_id, room=to_room_id)


class DataCombiner:
    def __init__(self, rooms: List[Dict[str, Any]], students: List[Dict[str, Any]]):
        self.rooms = rooms
        self.students = students

    def combine(self) -> List[Dict[str, Any]]:
        room_dict = {room['id']: {'id': room['id'], 'name': room['name'], 'students': []}
                     for room in self.rooms}

        for student in self.students:
            room_id = student['room']
            if room_id in room_dict:
                room_dict[room_id]['students'].append({
                    'id': student['id'],
                    'name': student['name']
                })

        return list(room_dict.values())


class JsonDataLoader:
    def load(self, file_path: str) -> List[Dict[str, Any]]:
        with open(file_path, 'r') as file:
            return json.load(file)


