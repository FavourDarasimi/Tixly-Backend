from django.urls import path
from .views import ListEvents,EventDetails,EventTicketTiers

urlpatterns = [
    path("events/",ListEvents.as_view()),
    path("event/<int:pk>/",EventDetails.as_view()),
    path("event/<int:pk>/ticket-tiers/",EventTicketTiers.as_view())
]