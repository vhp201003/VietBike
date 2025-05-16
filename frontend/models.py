from django.db import models
from django.conf import settings

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    is_driver = models.BooleanField(default=False)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    driver_license = models.ImageField(upload_to='driver_licenses/', blank=True, null=True)
    vehicle_photo = models.ImageField(upload_to='vehicle_photos/', blank=True, null=True)
    is_connected = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username
