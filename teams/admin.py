from django.contrib import admin

from .models import Team, Role, Member

admin.site.register(Team)
admin.site.register(Role)
admin.site.register(Member)
