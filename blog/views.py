from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost


def blog_list(request):
    posts = BlogPost.objects.all().order_by("-created_at")
    paginator = Paginator(posts, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "blog/home.html", {"page_obj": page_obj})


def blog_detail(request, slug):
    post = get_object_or_404(BlogPost, slug=slug)
    related_posts = (
        BlogPost.objects.filter(category=post.category)
        .exclude(id=post.id)
        .distinct()[:3]
    )
    context = {
        "post": post,
        "related_posts": related_posts,
    }
    return render(request, "blog/detail.html", context)
