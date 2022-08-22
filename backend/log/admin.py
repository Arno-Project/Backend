from django.contrib import admin

# Register your models here.
from log.models import Log

admin.site.register(Log)


class LogAdmin(admin.ModelAdmin):
    readonly_fields = ['level', 'source', 'message', 'created_at']
