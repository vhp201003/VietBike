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
    license_number = models.CharField(max_length=20, unique=True)
    is_available = models.BooleanField(default=True)
    rating = models.FloatField(default=5.0)
    driver_license = models.ImageField(upload_to='driver_licenses/', null=True, blank=True)
    vehicle_photo = models.ImageField(upload_to='vehicle_photos/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.license_number}"

class Vehicle(models.Model):
    driver = models.OneToOneField('DriverProfile', on_delete=models.CASCADE, related_name='vehicle')
    vehicle_type = models.CharField(max_length=20, default='bike', editable=False)
    license_plate = models.CharField(max_length=15, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()

    def __str__(self):
        return f"{self.brand} {self.model} ({self.license_plate})"

class Ride(models.Model):
    STATUS_CHOICES = [
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey('DriverProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='rides')
    start_location = models.CharField(max_length=255)
    end_location = models.CharField(max_length=255)
    fare = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=11, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Ride {self.id}: {self.start_location} to {self.end_location}"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('credit_card', 'Credit Card'),
        ('momo', 'Momo'),
    ]
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('completed', 'Completed')], default='pending')
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment {self.id} - {self.amount} {self.payment_method}"

class Rating(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='rating')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings')
    driver = models.ForeignKey('DriverProfile', on_delete=models.CASCADE, related_name='driver_ratings')
    score = models.FloatField()
    comment = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rating {self.score} for {self.driver.user.username}"

class RideLocation(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='locations')
    driver = models.ForeignKey('DriverProfile', on_delete=models.CASCADE, related_name='locations')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Location {self.latitude}, {self.longitude} for Ride {self.ride.id}"
