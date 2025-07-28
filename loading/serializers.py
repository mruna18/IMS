from rest_framework import serializers
from .models import Loading

class LoadingSerializer(serializers.ModelSerializer):
    outward_number = serializers.CharField(source='outward.id', read_only=True)

    class Meta:
        model = Loading
        fields = '__all__'