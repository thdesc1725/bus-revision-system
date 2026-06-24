from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import Bus, Book
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from datetime import datetime


def home(request):
    if request.user.is_authenticated:
        return render(request, "myapp/home.html")
    else:
        return render(request, "myapp/signin.html")


@login_required(login_url="signin")
def findbus(request):
    context = {}
    if request.method == "POST":
        source_r = request.POST.get("source")
        dest_r = request.POST.get("destination")
        date_r = request.POST.get("date")

        try:
            date_r = datetime.strptime(date_r, "%Y-%m-%d").date()
        except:
            context["error"] = "Please select a valid date"
            return render(request, "myapp/findbus.html", context)

        bus_list = Bus.objects.filter(source=source_r, dest=dest_r, date=date_r)

        if bus_list.exists():
            return render(request, "myapp/list.html", {"bus_list": bus_list})
        else:
            context["error"] = "Sorry no buses available"
            return render(request, "myapp/findbus.html", context)

    return render(request, "myapp/findbus.html")


@login_required(login_url="signin")
def bookings(request):
    """
    Step 1:
    Create booking with PENDING status
    and redirect user to payment page.
    """
    context = {}
    if request.method == "POST":
        try:
            bus_id = int(request.POST.get("bus_id"))
            seats_r = int(request.POST.get("no_seats"))
        except (TypeError, ValueError):
            context["error"] = "Invalid bus ID or seat count"
            return render(request, "myapp/findbus.html", context)

        if seats_r <= 0:
            context["error"] = "Number of seats must be greater than 0"
            return render(request, "myapp/findbus.html", context)

        try:
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            context["error"] = "Bus not found"
            return render(request, "myapp/findbus.html", context)

        if int(bus.rem) < seats_r:
            context["error"] = "Sorry, not enough seats available"
            return render(request, "myapp/findbus.html", context)

        total_cost = Decimal(seats_r) * bus.price

        # create booking as pending (do not reduce seats yet)
        book = Book.objects.create(
            name=request.user.username,
            email=request.user.email,
            userid=request.user.id,
            bus_name=bus.bus_name,
            source=bus.source,
            busid=bus.id,
            dest=bus.dest,
            price=bus.price,
            total_price=total_cost,
            nos=seats_r,
            date=bus.date,
            time=bus.time,
            status="PENDING",
            payment_status="PENDING",
        )

        return redirect("payment", booking_id=book.id)

    return render(request, "myapp/findbus.html")


@login_required(login_url="signin")
def payment_page(request, booking_id):
    """
    Step 2:
    Show payment page for pending booking.
    """
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)

    if book.status == "CONFIRMED":
        return render(request, "myapp/bookings.html", {"book": book, "cost": book.total_price})

    return render(request, "myapp/payment.html", {"book": book})


@login_required(login_url="signin")
def payment_success(request, booking_id):
    """
    Step 3:
    Demo payment success.
    On success:
    - check seat availability again
    - reduce seats
    - mark booking confirmed
    """
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)

    if book.status == "CONFIRMED":
        return render(request, "myapp/bookings.html", {"book": book, "cost": book.total_price})

    bus = get_object_or_404(Bus, id=book.busid)

    # re-check seats before confirming
    if int(bus.rem) < int(book.nos):
        book.status = "CANCELLED"
        book.payment_status = "FAILED"
        book.save()
        return render(request, "myapp/error.html", {
            "error": "Payment failed because seats are no longer available."
        })

    # reduce seats now
    bus.rem = int(bus.rem) - int(book.nos)
    bus.save()

    # confirm booking
    book.status = "CONFIRMED"
    book.payment_status = "PAID"
    book.payment_id = f"PAY{book.id}{request.user.id}"
    book.save()

    return render(request, "myapp/bookings.html", {
        "book": book,
        "cost": book.total_price
    })


@login_required(login_url="signin")
def payment_failed(request, booking_id):
    """
    Optional failure route.
    """
    book = get_object_or_404(Book, id=booking_id, userid=request.user.id)
    book.payment_status = "FAILED"
    book.status = "CANCELLED"
    book.save()

    return render(request, "myapp/error.html", {
        "error": "Payment failed or cancelled."
    })


@login_required(login_url="signin")
def cancellings(request):
    context = {}
    if request.method == "POST":
        booking_id = request.POST.get("bus_id")

        if not booking_id:
            context["error"] = "Invalid booking ID"
            return render(request, "myapp/error.html", context)

        try:
            book = Book.objects.get(id=int(booking_id), userid=request.user.id)

            # only restore seats if booking was confirmed
            if book.status == "CONFIRMED":
                bus = Bus.objects.get(id=book.busid)
                bus.rem = int(bus.rem) + int(book.nos)
                bus.save()

            book.status = "CANCELLED"
            book.payment_status = "REFUNDED" if book.payment_status == "PAID" else book.payment_status
            book.save()

            return redirect("seebookings")

        except Book.DoesNotExist:
            context["error"] = "Sorry, booking not found"
            return render(request, "myapp/error.html", context)

    return redirect("seebookings")


@login_required(login_url="signin")
def seebookings(request):
    context = {}
    id_r = request.user.id
    book_list = Book.objects.filter(userid=id_r).order_by('-id')

    if book_list.exists():
        return render(request, "myapp/booklist.html", {"book_list": book_list})
    else:
        context["error"] = "Sorry no buses booked"
        return render(request, "myapp/findbus.html", context)


def signup(request):
    context = {}
    if request.method == "POST":
        name_r = request.POST.get("name")
        email_r = request.POST.get("email")
        password_r = request.POST.get("password")

        if User.objects.filter(username=name_r).exists():
            context["error"] = "Username already exists"
            return render(request, "myapp/signup.html", context)

        user = User.objects.create_user(
            username=name_r,
            email=email_r,
            password=password_r,
        )

        if user:
            login(request, user)
            return render(request, "myapp/thank.html")
        else:
            context["error"] = "Provide valid credentials"
            return render(request, "myapp/signup.html", context)

    return render(request, "myapp/signup.html", context)


def signin(request):
    context = {}
    if request.method == "POST":
        name_r = request.POST.get("name")
        password_r = request.POST.get("password")
        user = authenticate(request, username=name_r, password=password_r)

        if user:
            login(request, user)
            context["user"] = name_r
            context["id"] = request.user.id
            return render(request, "myapp/success.html", context)
        else:
            context["error"] = "Provide valid credentials"
            return render(request, "myapp/signin.html", context)

    context["error"] = "You are not logged in"
    return render(request, "myapp/signin.html", context)


def signout(request):
    logout(request)
    return render(request, "myapp/signin.html", {"error": "You have been logged out"})


def success(request):
    context = {"user": request.user}
    return render(request, "myapp/success.html", context)