from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import *
from .serializers import *
from django.utils import timezone

class TaskTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_types = TaskType.objects.filter(deleted=False)
        serializer = TaskTypeSerializer(task_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PutAwayTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = PutAwayTask.objects.filter(assigned_to=request.user, is_completed=False, deleted=False)
        serializer = PutAwayTaskSerializer(tasks, many=True)
        return Response(serializer.data)

class PutAwayTaskCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            task = PutAwayTask.objects.get(pk=pk, assigned_to=request.user, deleted=False)
        except PutAwayTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        task.is_completed = True
        task.completed_at = timezone.now()
        task.updated_by = request.user
        task.save()

        return Response({"message": "Task marked as complete"}, status=status.HTTP_200_OK)


class PickUpTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = PickUpTask.objects.filter(assigned_to=request.user, is_completed=False, deleted=False)
        serializer = PickUpTaskSerializer(tasks, many=True)
        return Response(serializer.data)

class PickUpTaskCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            task = PickUpTask.objects.get(pk=pk, assigned_to=request.user, deleted=False)
        except PickUpTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=status.HTTP_404_NOT_FOUND)

        task.is_completed = True
        task.completed_at = timezone.now()
        task.updated_by = request.user
        task.save()

        return Response({"message": "Pickup task marked as complete"}, status=status.HTTP_200_OK)

class UserTaskDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        putaway_tasks = PutAwayTask.objects.filter(assigned_to=request.user, deleted=False)
        pickup_tasks = PickUpTask.objects.filter(assigned_to=request.user, deleted=False)

        putaway_serialized = PutAwayTaskSerializer(putaway_tasks, many=True)
        pickup_serialized = PickUpTaskSerializer(pickup_tasks, many=True)

        return Response({
            "putaway_tasks": putaway_serialized.data,
            "pickup_tasks": pickup_serialized.data,
        })
