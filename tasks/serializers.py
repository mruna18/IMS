from rest_framework import serializers
from .models import *

class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = '__all__'

# class PutAwayTaskSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PutAwayTask
#         fields = '__all__'  
#         read_only_fields = ('created_at', 'updated_at', 'completed_at')

# class PickUpTaskSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = PickUpTask
#         fields = '__all__'
#         read_only_fields = ('created_at', 'updated_at', 'completed_at')
        

class InventoryTaskSerializer(serializers.ModelSerializer):
    task_type_display = serializers.CharField(source='task_type.name', read_only=True)

    class Meta:
        model = InventoryTask
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def validate(self, data):
        task_type = data.get('task_type')
        code = task_type.code if task_type else None

        if not code:
            raise serializers.ValidationError("task_type is required.")

        if code == 'PUTAWAY':
            if not data.get('to_location'):
                raise serializers.ValidationError("PutAway task must have to_location.")
        elif code == 'PICKUP':
            if not data.get('from_location'):
                raise serializers.ValidationError("PickUp task must have from_location.")
        # You can add further types like 'MOVE', 'CYCLE_COUNT', etc.

        return data
