from django.db import models
from organizers.models import Event,TicketTier
from django.contrib.auth import get_user_model
user = get_user_model()


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    )

    order_id = models.UUIDField()
    user = models.ForeignKey(user, on_delete=models.PROTECT, related_name='orders')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    
    # Payment details
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, unique=True, null=True, blank=True) # Paystack/Stripe Ref
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"


class Ticket(models.Model):
    STATUS_CHOICES = (
        ('unused', 'Unused'),
        ('used', 'Used'),
        ('cancelled', 'Cancelled'),   
    )

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='tickets')
    event = models.ForeignKey(Event,on_delete=models.DO_NOTHING, related_name='event')
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='tickets')
    ticket_tier = models.ForeignKey(TicketTier, on_delete=models.CASCADE, related_name='tickets')
    qr_code = models.UUIDField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unused')
    used_at = models.DateTimeField(null=True, blank=True)
    attendee_name = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Ticket #{self.id} - {self.status}"
    

    class Meta:
        indexes = [
            models.Index(fields=['event']),
        ]


class SavedEvent(models.Model):
    user = models.ForeignKey(user, on_delete=models.CASCADE, related_name='saved_events')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='saved_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event')
# Create your models here.
