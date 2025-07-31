from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import *
from .serializers import *
from django.utils import timezone
from api.permission import check_employee_permission
from loading.models import Loading

class TaskTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_types = TaskType.objects.filter(deleted=False)
        serializer = TaskTypeSerializer(task_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PutAwayTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            putaway_type = TaskType.objects.get(code="PUTAWAY")
        except TaskType.DoesNotExist:
            return Response({"error": "PutAway task type not configured."}, status=500)

        tasks = InventoryTask.objects.filter(
            task_type=putaway_type,
            assigned_to=request.user,
            is_completed=False,
            deleted=False
        )
        serializer = InventoryTaskSerializer(tasks, many=True)
        return Response(serializer.data)

class PutAwayTaskCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("complete_putaway")
    def post(self, request, pk):
        try:
            task = InventoryTask.objects.get(pk=pk, assigned_to=request.user, deleted=False)
        except InventoryTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)

        if task.is_completed:
            return Response({"error": "Task already completed"}, status=400)

        task.is_completed = True
        task.completed_at = timezone.now()
        task.updated_by = request.user
        task.save()

        return Response({"message": "PutAway task marked as complete"}, status=200)

class PickUpTaskListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            pickup_type = TaskType.objects.get(code="PICKUP")
        except TaskType.DoesNotExist:
            return Response({"error": "PickUp task type not configured."}, status=500)

        tasks = InventoryTask.objects.filter(
            task_type=pickup_type,
            assigned_to=request.user,
            is_completed=False,
            deleted=False
        )
        serializer = InventoryTaskSerializer(tasks, many=True)
        return Response(serializer.data)

class PickUpTaskCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("complete_pickup")
    def post(self, request, pk):
        try:
            if request.user.is_superuser:
                task = InventoryTask.objects.get(pk=pk, deleted=False)
            else:
                task = InventoryTask.objects.get(pk=pk, assigned_to=request.user, deleted=False)
        except InventoryTask.DoesNotExist:
            return Response({"error": "Task not found"}, status=404)

        if task.is_completed:
            return Response({"error": "Task already completed"}, status=400)

        # Create loading record
        Loading.objects.create(
            outward=task.outward,
            item=task.item,
            quantity=task.quantity,
            loaded_by=request.user,
            remarks="Auto-logged from pickup task"
        )

        task.is_completed = True
        task.completed_at = timezone.now()
        task.updated_by = request.user
        task.save()

        return Response({"message": "Pickup task marked as complete"}, status=200)


class UserTaskDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = InventoryTask.objects.filter(assigned_to=request.user, deleted=False)

        putaway_type = TaskType.objects.filter(code="PUTAWAY").first()
        pickup_type = TaskType.objects.filter(code="PICKUP").first()

        putaway_tasks = tasks.filter(task_type=putaway_type) if putaway_type else []
        pickup_tasks = tasks.filter(task_type=pickup_type) if pickup_type else []

        putaway_serialized = InventoryTaskSerializer(putaway_tasks, many=True)
        pickup_serialized = InventoryTaskSerializer(pickup_tasks, many=True)

        return Response({
            "putaway_tasks": putaway_serialized.data,
            "pickup_tasks": pickup_serialized.data,
        })
