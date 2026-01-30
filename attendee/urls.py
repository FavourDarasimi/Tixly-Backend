from django.urls import path
from .views import ListEvents,EventDetails,EventTicketTiers,  UpcomingEvents,NewEvents,AttendeeEvents,EventTicket, SavedEventsList,RecommendedEvents


urlpatterns = [
    path("events/",ListEvents.as_view()),
    path("events/upcoming/", UpcomingEvents.as_view(), name="upcoming-events"),
    path("events/new/", NewEvents.as_view(), name="new-events"),
    path("events/recommended/", RecommendedEvents.as_view(), name="recommended-events"),
    path("event/<int:pk>/",EventDetails.as_view()),
    path("event/<int:pk>/ticket-tiers/",EventTicketTiers.as_view()),
    path("attendee/events/",AttendeeEvents.as_view()),
    path("events/saved/", SavedEventsList.as_view(), name="saved-events"),
    path("event/<int:pk>/ticket/",EventTicket.as_view())
]