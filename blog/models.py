from django.db import models
from taggit.managers import TaggableManager

# Create your models here.


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, null=True)
    content = models.TextField()
    image = models.ImageField(upload_to="blog_images/", blank=True, null=True, default='blog_images/default.jpg')
    category = models.CharField(max_length=100)
    tags = TaggableManager()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=200, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"
    



