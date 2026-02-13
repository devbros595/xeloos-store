from django.shortcuts import render, get_object_or_404, redirect
from .models import SIMCard, Country, NewsletterEmail, UserProfile
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from blog.models import BlogPost

# Create your views here.


@login_required
def user_profile_view(request):
    profile = request.user.userprofile

    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")

        request.user.email = email
        request.user.save()
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("user_profile")

    return render(request, "account/profile.html", {"profile": profile})


# Sign-Up View
def sign_up(request):
    if request.method == "POST":
        email = request.POST.get("email")
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Basic server-side validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("sign_up")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("sign_up")

        # Create the user
        user = User.objects.create_user(
            username=username, email=email, password=password
        )
        user.save()

        # Send Welcome Email

        # subject = 'Welcome to Break Digital Barriers!'
        # from_email = settings.DEFAULT_FROM_EMAIL
        # to = user.email

        # text_content = 'Hello {},\n\nThanks for signing up!'.format(user.username)
        # html_content = render_to_string('email/welcome_email.html', {'user': user})

        # msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
        # msg.attach_alternative(html_content, "text/html")
        # msg.send()

        messages.success(request, "Account created successfully!")
        return redirect("sign_in")  # Redirect to homepage or dashboard
    else:
        return render(request, "store/sign_up.html")  # Your HTML template path


# Sign-In View
def sign_in(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("index")  # Redirect to homepage or dashboard
        else:
            messages.error(request, "Invalid email or password.")
    return render(request, "store/sign_in.html")


# Sign-Out View
@login_required
def sign_out(request):
    logout(request)
    return redirect("sign_in")


def index(request):
    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "No email provided.")
            return redirect("index")  # Stop here

        if NewsletterEmail.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect("index")  # Stop here

        NewsletterEmail.objects.create(email=email)
        messages.success(request, "Subscribed successfully.")
        return redirect("index")

    recent_posts = BlogPost.objects.order_by("-created_at")[:3]
    country = Country.objects.all().order_by("name")
    return render(
        request, "store/index.html", {"country": country, "recent_posts": recent_posts}
    )


def store_category(request):
    country = Country.objects.all().order_by("name")
    return render(request, "store/store_category.html", {"categories": country})


def store(request, slug):
    sims = SIMCard.objects.all().order_by("name")
    paginator = Paginator(sims, 8)
    page_number = request.GET.get("page")
    store_obj = paginator.get_page(page_number)

    country = get_object_or_404(Country, slug=slug)
    simcard = SIMCard.objects.filter(country=country)

    context = {"page_obj": store_obj, "country_obj": simcard, "country": country}
    return render(request, "store/store.html", context)


def services(request):
    return render(request, "store/services.html")


def about_us(request):
    return render(request, "store/about_us.html")


def faqs(request):
    return render(request, "store/faqs.html")


def terms_view(request):
    return render(request, "store/terms-and-conditions.html")


def policy_view(request):
    return render(request, "store/privacy-policy.html")


@login_required
def user_profile_view(request):
    profile = request.user.userprofile

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        request.user.username = username
        profile.email = email
        profile.phone = phone
        request.user.save()
        profile.save()

        messages.success(request, "Profile updated successfully.")
        return redirect("user_profile")

    return render(request, "store/profile.html", {"profile": profile})


from orders.models import Order


@login_required
def order_history_view(request):
    orders = Order.objects.filter(email=request.user.email).order_by("-created_at")

    return render(request, "store/order_history.html", {"orders": orders})


@login_required
def order_detail_view(request, order_id):
    # Use user restriction for security
    order = get_object_or_404(Order, order_id=order_id, email=request.user.email)

    return render(request, "store/order_detail.html", {"order": order})


@login_required
def change_password_view(request):
    if request.method == "POST":
        current_password = request.POST.get("current_password")
        new_password = request.POST.get("new_password")

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
            return redirect("change_password")

        user.set_password(new_password)
        user.save()
        update_session_auth_hash(request, user)
        messages.success(request, "Your password has been updated successfully.")

        return redirect("change_password")

    return render(request, "store/change_password.html")
