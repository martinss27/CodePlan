from django.contrib import admin
from .models import JiraToken
# Register your models here.


@admin.register(JiraToken)
class JiraTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')