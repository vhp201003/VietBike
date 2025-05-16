from django.urls import path
from .views import UpdateProfileView
from .User.views import LoginView, RegisterView, LogoutView, UserProfileView, RegisterDriverView, ChangePasswordView
from .Vehicle.views import RegisterVehicleView, DeleteVehicleView
from .Ride.views import RequestRideView, ListRequestedRidesView, AcceptRideView, UpdateRideStatusView, TrackDriverLocationView

app_name = 'backend'
urlpatterns = [
    # User-related endpoints
    path("users/login/", LoginView.as_view(), name="login"),
    path("users/register/", RegisterView.as_view(), name="register"),
    path("users/logout/", LogoutView.as_view(), name="logout"),
    path("users/profile/", UserProfileView.as_view(), name="profile"),
    path("users/profile/update/", UpdateProfileView.as_view(), name="update_profile"),
    path("users/register-driver/", RegisterDriverView.as_view(), name="register_driver"),
    path("users/password/change/", ChangePasswordView.as_view(), name="change_password"), 
    
    # Vehicle-related endpoints
    path("vehicles/register/", RegisterVehicleView.as_view(), name="register_vehicle"), 
    path("vehicles/delete/", DeleteVehicleView.as_view(), name="delete_vehicle"),
    
    # Ride-related endpoints
    path("rides/request/", RequestRideView.as_view(), name="request_ride"),
    path("rides/requested/", ListRequestedRidesView.as_view(), name="list_requested_rides"),
    path("rides/accept/<int:ride_id>/", AcceptRideView.as_view(), name="accept_ride"),
    path("rides/update-status/<int:ride_id>/", UpdateRideStatusView.as_view(), name="update_ride_status"),
    path("rides/track-driver/<int:ride_id>/", TrackDriverLocationView.as_view(), name="track_driver_location"),
]
