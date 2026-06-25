import os
import qrcode
from decimal import Decimal
from datetime import datetime

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404

from .models import Bus, Book


# =========================
# HOME
# =========================
def home(request):
    if request.user.is_authenticated:
        bus_list = Bus.objects.all().order_by("date", "time")
        return render(request, "myapp/home.html", {"bus_list": bus_list})
    return render(request, "myapp/signin.html")


# =========================
# FIND BUS
# =========================
@login_required(login_url="signin")
def findbus(request):
    context = {}

    if request.method == "POST":
        source_r = request.POST.get("source")
        dest_r = request.POST.get("destination")
        date_r = request.POST.get("date")

        try:
            date_r = datetime.strptime(date_r, "%Y-%m-%d").date()
        except Exception:
            context["error"] = "Please select a valid date"
            return render(request, "myapp/findbus.html", context)

        bus_list = Bus.objects.filter(
            source__iexact=source_r,
            dest__iexact=dest_r,
            date=date_r
        ).order_by("time")

        if bus_list.exists():
            return render(request, "myapp/list.html", {"bus_list": bus_list})
        else:
            context["error"] = "Sorry, no buses available for selected route/date."
            return render(request, "myapp/findbus.html", context)

    return render(request, "myapp/findbus.html")


# =========================
# DIRECT RESERVE PAGE FROM HOME
# =========================
@login_required(login_url="signin")
def reserve_bus(request, bus_id):
    bus = get_object_or_404(Bus, id=bus_id)
    return render(request, "myapp/list.html", {
        "bus_list": [bus]
    })


# =========================
# CREATE BOOKING -> PAYMENT PAGE
# =========================
@login_required(login_url="signin")
def bookings(request):
    context = {}

    if request.method == "POST":
        try:
            bus_id = int(request.POST.get("bus_id"))
            seats_r = int(request.POST.get("no_seats"))
        except (TypeError, ValueError):
            context["error"] = "Invalid bus ID or seat count"
            return render(request, "myapp/error.html", context)

        if seats_r <= 0:
            context["error"] = "Seat count must be greater than 0"
            return render(request, "myapp/error.html", context)

        try:
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            context["error"] = "Bus not found"
            return render(request, "myapp/error.html", context)

        if int(bus.rem) < seats_r:
            context["error"] = "Sorry, not enough seats available"
            return render(request, "myapp/error.html", context)

        if not request.user.email:
            context["error"] = "Your account does not have an email address."
            return render(request, "myapp/error.html", context)

        total_cost = Decimal(seats_r) * bus.price

        # Create booking in pending state
        book = Book.objects.create(
            email=request.user.email,
            name=request.user.username,
            userid=request.user.id,
            busid=bus.id,
            bus_name=bus.bus_name,
            source=bus.source,
            dest=bus.dest,
            nos=seats_r,
            price=bus.price,
            total_price=total_cost,
            date=bus.date,
            time=bus.time,
            status=Book.PENDING,
            payment_status=Book.PAYMENT_PENDING,
        )

        messages.success(request, "Booking created successfully. Please complete payment.")
        return redirect("payment", booking_id=book.id)

    return redirect("home")


# =========================
# PAYMENT PAGE WITH UPI QR
# =========================
@login_required(login_url="signin")
def payment_page(request, booking_id):
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)

    if book.status == Book.CONFIRMED:
        messages.success(request, "This booking is already confirmed.")
        return redirect("seebookings")

    upi_id = "yourupi@oksbi"   # Replace with your real UPI ID
    payee_name = "TravelMate"

    upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&am={book.total_price}&cu=INR&tn=Booking#{book.id}"

    qr_folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(qr_folder, exist_ok=True)

    qr_filename = f"booking_{book.id}.png"
    qr_path = os.path.join(qr_folder, qr_filename)

    if not os.path.exists(qr_path):
        qr_img = qrcode.make(upi_link)
        qr_img.save(qr_path)

    qr_url = settings.MEDIA_URL + "qr_codes/" + qr_filename

    return render(request, "myapp/payment.html", {
        "book": book,
        "qr_url": qr_url,
        "upi_id": upi_id,
    })


# =========================
# SUBMIT PAYMENT PROOF
# =========================
@login_required(login_url="signin")
def submit_payment(request, booking_id):
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)

    if request.method != "POST":
        return redirect("payment", booking_id=book.id)

    upi_reference = request.POST.get("upi_reference")
    screenshot = request.FILES.get("payment_screenshot")

    upi_id = "yourupi@oksbi"
    payee_name = "TravelMate"
    upi_link = f"upi://pay?pa={upi_id}&pn={payee_name}&am={book.total_price}&cu=INR&tn=Booking#{book.id}"

    qr_folder = os.path.join(settings.MEDIA_ROOT, "qr_codes")
    os.makedirs(qr_folder, exist_ok=True)

    qr_filename = f"booking_{book.id}.png"
    qr_path = os.path.join(qr_folder, qr_filename)

    if not os.path.exists(qr_path):
        qr_img = qrcode.make(upi_link)
        qr_img.save(qr_path)

    qr_url = settings.MEDIA_URL + "qr_codes/" + qr_filename

    if not upi_reference or not screenshot:
        return render(request, "myapp/payment.html", {
            "book": book,
            "qr_url": qr_url,
            "upi_id": upi_id,
            "error": "Please enter UPI reference number and upload screenshot."
        })

    book.upi_reference = upi_reference
    book.payment_screenshot = screenshot
    book.payment_status = Book.PAYMENT_PENDING_VERIFICATION
    book.save()

    messages.success(request, "Payment proof submitted successfully. Waiting for admin verification.")
    return redirect("seebookings")


# =========================
# PAYMENT FAILED / CANCEL BEFORE APPROVAL
# =========================
@login_required(login_url="signin")
def payment_failed(request, booking_id):
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)

    if book.status == Book.CONFIRMED:
        return render(request, "myapp/error.html", {
            "error": "This booking is already confirmed and cannot be cancelled."
        })

    book.payment_status = Book.PAYMENT_FAILED
    book.status = Book.CANCELLED
    book.save()

    return render(request, "myapp/error.html", {
        "error": "Payment cancelled."
    })


# =========================
# CANCEL BOOKING
# =========================
@login_required(login_url="signin")
def cancellings(request):
    context = {}

    if request.method == "POST":
        booking_id = request.POST.get("booking_id")

        if not booking_id:
            context["error"] = "Invalid booking ID"
            return render(request, "myapp/error.html", context)

        try:
            book = Book.objects.get(id=int(booking_id), userid=request.user.id)

            if book.status == Book.CANCELLED:
                return render(request, "myapp/error.html", {
                    "error": "This booking is already cancelled."
                })

            if book.status == Book.CONFIRMED:
                bus = Bus.objects.get(id=book.busid)
                bus.rem = int(bus.rem) + int(book.nos)
                bus.save()

            book.status = Book.CANCELLED

            if book.payment_status == Book.PAYMENT_PAID:
                book.payment_status = Book.PAYMENT_REFUNDED

            book.save()
            messages.success(request, "Booking cancelled successfully.")
            return redirect("seebookings")

        except Book.DoesNotExist:
            context["error"] = "Sorry, booking not found"
            return render(request, "myapp/error.html", context)

    return redirect("seebookings")


# =========================
# VIEW USER BOOKINGS
# =========================
@login_required(login_url="signin")
def seebookings(request):
    book_list = Book.objects.filter(userid=request.user.id).order_by("-id")
    return render(request, "myapp/booklist.html", {"book_list": book_list})


# =========================
# SIGNUP
# =========================
def signup(request):
    # if already logged in, don't show signup again
    if request.user.is_authenticated:
        return redirect("home")

    context = {}

    if request.method == "POST":
        name_r = request.POST.get("name", "").strip()
        email_r = request.POST.get("email", "").strip()
        password_r = request.POST.get("password", "").strip()

        if not name_r or not email_r or not password_r:
            context["error"] = "All fields are required"
            return render(request, "myapp/signup.html", context)

        if User.objects.filter(username=name_r).exists():
            context["error"] = "Username already exists"
            return render(request, "myapp/signup.html", context)

        if User.objects.filter(email=email_r).exists():
            context["error"] = "Email already registered"
            return render(request, "myapp/signup.html", context)

        user = User.objects.create_user(
            username=name_r,
            email=email_r,
            password=password_r,
        )

        # auto login after signup
        login(request, user)

        # thank page show after signup
        return render(request, "myapp/thank.html", {
            "user": user.username
        })

    return render(request, "myapp/signup.html", context)


# =========================
# SIGNIN
# =========================
def signin(request):
    # if already logged in, don't show signin again
    if request.user.is_authenticated:
        return redirect("home")

    context = {}

    if request.method == "POST":
        name_r = request.POST.get("name", "").strip()
        password_r = request.POST.get("password", "").strip()

        if not name_r or not password_r:
            context["error"] = "Please enter username and password"
            return render(request, "myapp/signin.html", context)

        user = authenticate(request, username=name_r, password=password_r)

        if user:
            login(request, user)
            return render(request, "myapp/success.html", {
                "user": user.username,
                "id": user.id
            })
        else:
            context["error"] = "Provide valid credentials"
            return render(request, "myapp/signin.html", context)

    return render(request, "myapp/signin.html", context)


# =========================
# SIGNOUT
# =========================
def signout(request):
    logout(request)
    return render(request, "myapp/signin.html", {
        "error": "You have been logged out"
    })


# =========================
# SUCCESS PAGE
# =========================
@login_required(login_url="signin")
def success(request):
    return render(request, "myapp/success.html", {
        "user": request.user.username,
        "id": request.user.id
    })