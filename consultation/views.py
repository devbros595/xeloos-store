from django.shortcuts import render, redirect
from django.core.mail import send_mail
from django.conf import settings
from .models import Consultation

def book_consultation(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        phone = request.POST.get("phone")
        message = request.POST.get("message")

        # Save to database
        Consultation.objects.create(name=name, email=email, subject=subject, phone=phone, message=message)

        # Send confirmation email
        # send_mail(
        #     "Consultation Booking Confirmation",
        #     f"Hi {name},\n\nYour consultation request has been received. We’ll contact you soon!",
        #     settings.DEFAULT_FROM_EMAIL,
        #     [email],
        #     fail_silently=False,
        # )

        # Notify admin
        # send_mail(
        #     "New Consultation Request",
        #     f"A new consultation has been requested by {name}.\n\nEmail: {email}\nPhone: {phone}\n\nMessage:\n{message}",
        #     settings.DEFAULT_FROM_EMAIL,
        #     ["your_admin_email@gmail.com"],
        #     fail_silently=False,
        # )

        return redirect("consultation_success")
    
    return render(request, "consultation/consultation.html")

def consultation_success(request):
    return render(request, "consultation/success.html")
