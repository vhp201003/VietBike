from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=False)
    phone = models.CharField(max_length=15, unique=True)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone']

    def __str__(self):
        return self.username

class DriverProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driverprofile')
    id_number = models.CharField(max_length=12, unique=True)
    license_number = models.CharField(max_length=20, unique=True)
    license_plate = models.CharField(max_length=10, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    driver_license = models.ImageField(upload_to='driver_licenses/')
    vehicle_photo = models.ImageField(upload_to='vehicle_photos/')
    is_available = models.BooleanField(default=False)
    rating = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} - Driver Profile"

class Ride(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ride {self.id} - {self.user.username}"

class RideLocation(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='locations')
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location for Ride {self.ride.id}"

class Rating(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.score} for Ride {self.ride.id}"
