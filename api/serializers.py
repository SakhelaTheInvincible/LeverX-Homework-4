from __future__ import annotations

from rest_framework import serializers


class RoomSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="Unique room identifier")
    name = serializers.CharField(max_length=255, help_text="Room name")


class StudentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="Unique student identifier")
    name = serializers.CharField(max_length=255, help_text="Full name")
    room = serializers.IntegerField(help_text="Room id the student belongs to")
    sex = serializers.ChoiceField(choices=["M", "F"], help_text='Sex of the student: "M" or "F"')
    birthday = serializers.DateTimeField(
        format="%Y-%m-%dT%H:%M:%S.%f",
        input_formats=["%Y-%m-%dT%H:%M:%S.%f"],
        help_text="Birthday in ISO-like format YYYY-MM-DDTHH:MM:SS.ffffff",
    )


class MoveStudentSerializer(serializers.Serializer):
    to_room_id = serializers.IntegerField()


class ErrorResponseSerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.DictField(child=serializers.CharField(), required=False)


class StudentInRoomSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)


class CombinedRoomSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(max_length=255)
    students = StudentInRoomSerializer(many=True)


