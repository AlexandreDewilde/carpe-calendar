from django.shortcuts import render, redirect

from .models import Team


def current(request):
    last_team = Team.objects.latest("year")
    return redirect(f"/teams/{last_team.year}")


def team_year(request, year):
    team = Team.objects.get(year=year)
    return render(request, "team.html", {"team": team})
