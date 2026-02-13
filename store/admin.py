from django.contrib import admin
from .models import SIMCard, UserProfile, Country, NewsletterEmail

@admin.register(SIMCard)
class SIMCardAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "country")
    search_fields = ("name",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "user")


admin.site.register(Country)
admin.site.register(NewsletterEmail)
