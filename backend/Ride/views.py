from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from backend.models import Ride, DriverProfile, RideLocation, Rating
from django.utils import timezone
from django.db.models import Q
from django.db import models
import random

class RequestRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể yêu cầu chuyến.'}, status=status.HTTP_403_FORBIDDEN)

        start_location = request.data.get('start_location')
        end_location = request.data.get('end_location')

        if not all([start_location, end_location]):
            return Response({'error': 'Vui lòng cung cấp điểm bắt đầu và điểm kết thúc.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tính giá vé giả lập
        fare = round(random.uniform(50000, 200000), 2)

        ride = Ride.objects.create(
            user=user,
            start_location=start_location,
            end_location=end_location,
            fare=fare,
            status='requested'
        )

        return Response({
            'message': 'Yêu cầu chuyến thành công!',
            'ride': {
                'id': ride.id,
                'start_location': ride.start_location,
                'end_location': ride.end_location,
                'fare': float(ride.fare),
                'status': ride.status,
                'requested_at': ride.requested_at
            }
        }, status=status.HTTP_201_CREATED)

class ListRequestedRidesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể xem danh sách chuyến yêu cầu.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
            if not driver_profile.vehicle:
                return Response({'error': 'Bạn chưa đăng ký phương tiện.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        rides = Ride.objects.filter(status='requested')
        rides_data = [{
            'id': ride.id,
            'start_location': ride.start_location,
            'end_location': ride.end_location,
            'fare': float(ride.fare),
            'requested_at': ride.requested_at,
            'customer': ride.user.username
        } for ride in rides]

        return Response({
            'message': 'Danh sách chuyến yêu cầu.',
            'rides': rides_data
        }, status=status.HTTP_200_OK)

class AcceptRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể chấp nhận chuyến.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
            if not driver_profile.vehicle:
                return Response({'error': 'Bạn chưa đăng ký phương tiện.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = Ride.objects.get(id=ride_id, status='requested')
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc đã được chấp nhận.'}, status=status.HTTP_404_NOT_FOUND)

        if driver_profile.rides.filter(status__in=['accepted', 'in_progress']).exists():
            return Response({'error': 'Bạn đang thực hiện một chuyến khác.'}, status=status.HTTP_400_BAD_REQUEST)

        ride.driver = driver_profile
        ride.status = 'accepted'
        ride.save()

        return Response({
            'message': 'Chấp nhận chuyến thành công!',
            'ride': {
                'id': ride.id,
                'start_location': ride.start_location,
                'end_location': ride.end_location,
                'fare': float(ride.fare),
                'status': ride.status,
                'customer': ride.user.username
            }
        }, status=status.HTTP_200_OK)

class UpdateRideStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, ride_id):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể cập nhật trạng thái chuyến.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = Ride.objects.get(id=ride_id, driver=driver_profile)
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)

        status = request.data.get('status')
        valid_statuses = ['in_progress', 'completed', 'cancelled']
        if status not in valid_statuses:
            return Response({'error': f'Trạng thái phải là một trong: {", ".join(valid_statuses)}.'}, status=status.HTTP_400_BAD_REQUEST)

        if ride.status == 'completed' or ride.status == 'cancelled':
            return Response({'error': 'Chuyến đi đã hoàn thành hoặc bị hủy.'}, status=status.HTTP_400_BAD_REQUEST)

        ride.status = status
        if status == 'completed':
            ride.completed_at = timezone.now()
        ride.save()

        return Response({
            'message': 'Cập nhật trạng thái chuyến thành công!',
            'ride': {
                'id': ride.id,
                'start_location': ride.start_location,
                'end_location': ride.end_location,
                'fare': float(ride.fare),
                'status': ride.status
            }
        }, status=status.HTTP_200_OK)

class TrackDriverLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ride_id):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể theo dõi vị trí tài xế.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            ride = Ride.objects.get(id=ride_id, user=user, status__in=['accepted', 'in_progress'])
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)

        if not ride.driver:
            return Response({'error': 'Chuyến đi chưa có tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        latest_location = RideLocation.objects.filter(ride=ride, driver=ride.driver).order_by('-timestamp').first()
        if not latest_location:
            return Response({'error': 'Không có dữ liệu vị trí hiện tại.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Vị trí tài xế hiện tại.',
            'location': {
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'timestamp': latest_location.timestamp
            }
        }, status=status.HTTP_200_OK)

class RateRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể đánh giá chuyến đi.'}, status=status.HTTP_403_FORBIDDEN)

        ride_id = request.data.get('ride_id')
        score = request.data.get('score')
        comment = request.data.get('comment')

        if not all([ride_id, score]):
            return Response({'error': 'Vui lòng cung cấp ID chuyến đi và điểm đánh giá.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            score = float(score)
            if score < 1 or score > 5:
                return Response({'error': 'Điểm đánh giá phải từ 1 đến 5.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Điểm đánh giá phải là số.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = Ride.objects.get(id=ride_id, user=user, status='completed')
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại, chưa hoàn thành hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)

        if Rating.objects.filter(ride=ride).exists():
            return Response({'error': 'Chuyến đi này đã được đánh giá.'}, status=status.HTTP_400_BAD_REQUEST)

        rating = Rating.objects.create(
            ride=ride,
            user=user,
            driver=ride.driver,
            score=score,
            comment=comment
        )

        # Cập nhật rating trung bình của tài xế
        driver_ratings = ride.driver.ratings.all()
        average_rating = driver_ratings.aggregate(models.Avg('score'))['score__avg']
        ride.driver.rating = round(average_rating, 1) if average_rating else 0.0
        ride.driver.save()

        return Response({
            'message': 'Đánh giá chuyến đi thành công!',
            'rating': {
                'ride_id': ride.id,
                'score': rating.score,
                'comment': rating.comment,
                'created_at': rating.created_at
            }
        }, status=status.HTTP_201_CREATED)
