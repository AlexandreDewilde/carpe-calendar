from django.urls import path
from . import views

urlpatterns = [
    path("current", views.current, name="teams/current"),
    path("<int:year>", views.team_year, name="teams/team_year"),
]
