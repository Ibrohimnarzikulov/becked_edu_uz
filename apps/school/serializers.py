"""Serializers for school app."""
from rest_framework import serializers

from .models import Subject, Assignment, Circle


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('id', 'name', 'icon', 'progress')


class AssignmentSerializer(serializers.ModelSerializer):
    subject = serializers.IntegerField(source='subject_id', read_only=True)

    class Meta:
        model = Assignment
        fields = ('id', 'title', 'subject', 'status', 'created_at')


class CircleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Circle
        fields = ('id', 'name', 'icon', 'members', 'schedule')
