from django.urls import path
from .User.views import LoginView, RegisterView, LogoutView, UserProfileView, RegisterDriverView
from .Vehicle.views import RegisterVehicleView, DeleteVehicleView
from .Ride.views import RequestRideView, ListRequestedRidesView, AcceptRideView, UpdateRideStatusView, TrackDriverLocationView

urlpatterns = [
    #user
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("register-driver/", RegisterDriverView.as_view(), name="update-profile"),
    
    #vehicle
    path("register-vehicle/", RegisterVehicleView.as_view(), name="register-vehicle"), 
    path("delete-vehicle/", DeleteVehicleView.as_view(), name="delete-vehicle"),
    
    #ride
    path('rides/request/', RequestRideView.as_view(), name='request-ride'),
    path('rides/requested/', ListRequestedRidesView.as_view(), name='list-requested-rides'),
    path('rides/accept/<int:ride_id>/', AcceptRideView.as_view(), name='accept-ride'),
    path('rides/update-status/<int:ride_id>/', UpdateRideStatusView.as_view(), name='update-ride-status'),
    path('rides/track-driver/<int:ride_id>/', TrackDriverLocationView.as_view(), name='track-driver-location'),
]   
