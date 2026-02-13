from django.contrib import admin
from .models import Consultation

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "sent_at")
    search_fields = ("name", "email", "message")
    list_filter = ("sent_at",)

