from django.urls import path
from .views import ListEvents,EventDetails,EventTicketTiers,  UpcomingEvents,NewEvents

urlpatterns = [
    path("events/",ListEvents.as_view()),
    path("events/upcoming/", UpcomingEvents.as_view(), name="upcoming-events"),
    path("events/new/", NewEvents.as_view(), name="new-events"),
    path("event/<int:pk>/",EventDetails.as_view()),
    path("event/<int:pk>/ticket-tiers/",EventTicketTiers.as_view())
]