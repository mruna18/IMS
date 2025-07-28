from rest_framework import serializers
from .models import *

class TaskTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskType
        fields = '__all__'

class PutAwayTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PutAwayTask
        fields = '__all__'  
        read_only_fields = ('created_at', 'updated_at', 'completed_at')

class PickUpTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = PickUpTask
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'completed_at')
        

