from django.db import models
from django.contrib.auth.models import AbstractUser 

class User(AbstractUser):
    ROLES = (
        ("attendee","Attendee"),
        ("organizer","Organizer")
    )

    first_name = models.CharField(max_length=30)   
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    role = models.CharField(choices=ROLES,default="Attendee")

    USERNAME_FIELD = 'email'
    
    REQUIRED_FIELDS = ['username','first_name',"last_name","role"]

    def __str__(self):
        return self.username

# Create your models here.
