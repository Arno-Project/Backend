from django.contrib import admin

# Register your models here.
from notification import models

admin.site.register(models.Notification)
