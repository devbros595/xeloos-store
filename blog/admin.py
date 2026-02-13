from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "created_at")
    search_fields = ("title", "author")
    ordering = ("-created_at",)
    list_filter = ("created_at", "author")
    prepopulated_fields = {"slug": ("title",)}
