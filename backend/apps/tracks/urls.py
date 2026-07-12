from django.urls import path
from . import views

app_name = "tracks"

urlpatterns = [
    path("", views.track_list, name="track-list"),
    path("mine/", views.my_tracks, name="my-tracks"),
    path("categories/", views.track_categories, name="categories"),
    path("<slug:slug>/", views.track_detail, name="track-detail"),
    path("<slug:slug>/enroll/", views.enroll_in_track, name="enroll"),
    path("<slug:slug>/progress/", views.update_track_progress, name="progress"),
]
