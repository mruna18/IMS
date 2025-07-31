from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from .models import Loading
from .serializers import LoadingSerializer
from inventory.models import Outward
from tasks.models import PickUpTask
from api.permission import check_employee_permission


class LoadingStartView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("start_loading")
    def post(self, request):
        data = request.data.copy()
        outward_id = data.get("outward")

        # Manual outward validation
        try:
            outward = Outward.objects.get(id=outward_id, deleted=False)
        except Outward.DoesNotExist:
            return Response(
                {"error": "Outward with this ID does not exist or has been deleted."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data['created_by'] = request.user.id
        data['updated_by'] = request.user.id

        serializer = LoadingSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Loading started", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class LoadingCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    # @check_employee_permission("complete_loading")
    def post(self, request, pk):
        try:
            loading = Loading.objects.get(pk=pk, deleted=False)
        except Loading.DoesNotExist:
            return Response({"error": "Loading entry not found"}, status=status.HTTP_404_NOT_FOUND)

        loading.is_completed = True
        loading.completed_at = timezone.now()
        loading.loaded_at = timezone.now()
        loading.loaded_by = request.user
        loading.vehicle_number = request.data.get("vehicle_number", loading.vehicle_number)
        loading.driver_name = request.data.get("driver_name", loading.driver_name)
        loading.remarks = request.data.get("remarks", loading.remarks)
        loading.updated_by = request.user
        loading.save()

        # Mark outward as dispatched
        outward = loading.outward
        if outward:
            outward.is_dispatched = True
            outward.dispatched_at = timezone.now()
            outward.save()

        # Mark pickup task as complete if not already
        pickup_task = PickUpTask.objects.filter(outward=outward, is_completed=False).first()
        if pickup_task:
            pickup_task.is_completed = True
            pickup_task.completed_at = timezone.now()
            pickup_task.save()

        return Response({"message": "Loading marked as complete and outward dispatched"}, status=status.HTTP_200_OK)


class LoadingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        outward_id = request.query_params.get("outward_id")
        is_completed = request.query_params.get("is_completed")

        queryset = Loading.objects.filter(deleted=False)

        if outward_id:
            queryset = queryset.filter(outward__id=outward_id)
        if is_completed is not None:
            queryset = queryset.filter(is_completed=is_completed.lower() == "true")

        serializer = LoadingSerializer(queryset.order_by('-id'), many=True)
        return Response(serializer.data)
