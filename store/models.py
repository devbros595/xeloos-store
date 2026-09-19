from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    username = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return f"{self.username}'s Profile"


class Country(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="flags/")
    slug = models.SlugField(blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Country.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "countries"


class SIMCard(models.Model):
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="simcards/")
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.country}"


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="categories/",
        blank=True,
        null=True
    )
    icon = models.CharField(
        max_length=100,
        blank=True,
        help_text="Font Awesome icon class, e.g. fas fa-sim-card"
    )
    is_active = models.BooleanField(default=True)
    ordering = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["ordering", "name"]
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        slug = base_slug
        counter = 1

        while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        self.slug = slug

        super().save(*args, **kwargs)
    def __str__(self):
        return self.name

class StoreSettings(models.Model):
    esim_category = models.OneToOneField(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="esim_store_setting",
    )

    physical_sim_category = models.OneToOneField(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="physical_sim_store_setting",
    )

    internet_tools_category = models.OneToOneField(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="internet_tools_store_setting",
    )

    privacy_tools_category = models.OneToOneField(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="privacy_tools_store_setting",
    )

    def __str__(self):
        return "Store Settings"


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="products"
    )

    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="products"
    )

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to="products/")
    description = models.TextField()
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1

            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class NewsletterEmail(models.Model):
    email = models.EmailField(max_length=100)

    def __str__(self):
        return self.email