from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.utils import timezone
from backend.models import Ride, DriverProfile, RideLocation, Payment, Rating
import logging

logger = logging.getLogger(__name__)

class RequestRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.role != "customer":
            return Response(
                {"error": "Chức năng này chỉ dành cho customer"},
                status=status.HTTP_403_FORBIDDEN
            )

        start_location = request.data.get("start_location")
        end_location = request.data.get("end_location")
        
        if not start_location or not end_location:
            return Response(
                {"error": "Thiếu start_location hoặc end_location"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            ride = Ride.objects.create(
                user=request.user,
                start_location=start_location,
                end_location=end_location,
                status='requested',
                fare=10000.00  # Placeholder fare calculation
            )
            logger.debug(f"Ride created: {ride.id}")
            Payment.objects.create(
                ride=ride,
                user=request.user,
                amount=ride.fare,
                payment_method='cash',
                status='pending'
            )
            return Response(
                {
                    "message": "Tạo yêu cầu chuyến đi thành công",
                    "ride_id": ride.id,
                    "start_location": ride.start_location,
                    "end_location": ride.end_location,
                    "status": ride.status,
                    "fare": ride.fare
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            logger.error(f"Error creating ride: {str(e)}")
            return Response({"error": f"Lỗi tạo chuyến đi: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ListRequestedRidesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.role != 'driver':
            return Response(
                {"error": "Chức năng này chỉ dành cho tài xế"},
                status=status.HTTP_403_FORBIDDEN
            )

        rides = Ride.objects.filter(status='requested', driver__isnull=True)
        data = [{
            "ride_id": ride.id,
            "start_location": ride.start_location,
            "end_location": ride.end_location,
            "user_id": ride.user.id,
            "requested_at": ride.requested_at,
            "fare": ride.fare
        } for ride in rides]
        return Response(data, status=status.HTTP_200_OK)

class AcceptRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        if request.user.role != "driver":
            return Response(
                {"error": "Chức năng này chỉ dành cho tài xế"},
                status=status.HTTP_403_FORBIDDEN
            )

        ride = get_object_or_404(Ride, id=ride_id)
        if ride.status != 'requested' or ride.driver is not None:
            return Response(
                {"error": "Chuyến này không thể nhận (đã có tài xế hoặc không còn requested)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return Response({"error": "Bạn chưa có DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        ride.driver = driver_profile
        ride.status = 'accepted'
        ride.save()
        logger.debug(f"Ride accepted: {ride.id} by driver: {driver_profile.id}")
        return Response(
            {
                "message": "Nhận chuyến thành công",
                "ride_id": ride.id,
                "status": ride.status,
                "driver": ride.driver.user.email
            },
            status=status.HTTP_200_OK
        )

class UpdateRideStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        ride = get_object_or_404(Ride, id=ride_id)
        new_status = request.data.get("status")

        if not new_status:
            return Response({"error": "Thiếu status mới"}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.role != 'driver':
            return Response({"error": "Chỉ tài xế được cập nhật"}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = DriverProfile.objects.get(user=request.user)
        except DriverProfile.DoesNotExist:
            return Response({"error": "Bạn chưa có DriverProfile"}, status=status.HTTP_404_NOT_FOUND)

        if ride.driver != driver_profile:
            return Response({"error": "Bạn không phải tài xế của chuyến này"}, status=status.HTTP_403_FORBIDDEN)

        if new_status not in ['accepted', 'in_progress', 'completed', 'cancelled']:
            return Response({"error": "Trạng thái không hợp lệ"}, status=status.HTTP_400_BAD_REQUEST)

        ride.status = new_status
        if new_status == 'completed':
            ride.completed_at = timezone.now()
            payment = ride.payment
            payment.status = 'completed'
            payment.paid_at = timezone.now()
            payment.save()
            # Create placeholder rating (customer must update later)
            Rating.objects.get_or_create(
                ride=ride,
                user=ride.user,
                driver=driver_profile,
                defaults={'score': 5.0}
            )
        ride.save()
        logger.debug(f"Ride status updated: {ride.id} to {new_status}")
        return Response({
            "message": "Cập nhật trạng thái thành công",
            "ride_id": ride.id,
            "status": ride.status
        }, status=status.HTTP_200_OK)

class TrackDriverLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ride_id):
        ride = get_object_or_404(Ride, id=ride_id)
        if request.user != ride.user and (not ride.driver or request.user != ride.driver.user):
            return Response({"error": "Bạn không có quyền xem vị trí chuyến này"}, status=status.HTTP_403_FORBIDDEN)

        locations = RideLocation.objects.filter(ride=ride).order_by('-timestamp')
        if not locations.exists():
            return Response({"message": "Chưa có tọa độ nào"}, status=status.HTTP_404_NOT_FOUND)

        latest_location = locations.first()
        data = {
            "ride_id": ride.id,
            "driver_id": ride.driver.id if ride.driver else None,
            "latitude": latest_location.latitude,
            "longitude": latest_location.longitude,
            "timestamp": latest_location.timestamp
        }
        return Response(data, status=status.HTTP_200_OK)
