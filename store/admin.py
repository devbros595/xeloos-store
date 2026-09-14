from django.contrib import admin
from .models import (
    SIMCard,
    UserProfile,
    Country,
    NewsletterEmail,
    Category,
    Product,
)


@admin.register(SIMCard)
class SIMCardAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "country")
    search_fields = ("name",)
    list_filter = ("country",)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "user")
    search_fields = ("username", "email")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "slug",
        "is_active",
        "ordering",
    )
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    prepopulated_fields = {
        "slug": ("name",)
    }
    ordering = ("ordering", "name")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "featured",
        "is_active",
        "created_at",
    )
    list_filter = (
        "category",
        "featured",
        "is_active",
    )
    search_fields = (
        "name",
        "description",
    )
    prepopulated_fields = {
        "slug": ("name",)
    }
    list_editable = (
        "price",
        "featured",
        "is_active",
    )


admin.site.register(Country)
admin.site.register(NewsletterEmail)