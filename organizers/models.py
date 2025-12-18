from django.db import models
from cloudinary.models import CloudinaryField
from django.contrib.auth import get_user_model
user = get_user_model()



class Event(models.Model):
    CATEGORY_CHOICES = (
        ('music', 'Music'),
        ('sports', 'Sports'),
        ('conference', 'Conference'),
        ('workshop', 'Workshop'),
        ('festival', 'Festival'),
        ('theater', 'Theater'),
        ('tech', 'Tech'),
        ('other', 'Other'),
    )

    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    image = CloudinaryField('image')
    category = models.CharField(choices=CATEGORY_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateField(null=True, blank=True)
    startDateTime = models.DateTimeField(null=True, blank=True)
    endDateTime = models.DateTimeField(null=True, blank=True)
    time = models.TimeField()
    location = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    available_tickets = models.IntegerField()
    organizer = models.ForeignKey(user, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class TicketTier(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_tiers')
    total_tickets = models.IntegerField()
    available_tickets = models.IntegerField()
    salesStart = models.DateTimeField()
    saleEnd = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.event.title} - {self.name}'

class Coupon(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='coupons')
    code = models.CharField(max_length=20)
    discount_percentage = models.PositiveIntegerField(default=0) # e.g., 10 for 10% off
    fixed_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True) # e.g., remove $5
    
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=100)
    times_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code


# Create your models here.
