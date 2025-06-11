from rest_framework import serializers
from backend.apps.tasks.models import Task, TaskStatus

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'source', 'created_at']
        read_only_fields = ['id', 'created_at']