from __future__ import annotations

from rest_framework import serializers


class RoomSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)


class StudentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(max_length=255)
    room = serializers.IntegerField()


class MoveStudentSerializer(serializers.Serializer):
    to_room_id = serializers.IntegerField()


class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(child=serializers.CharField(), required=False)


