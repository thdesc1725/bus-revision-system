from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),

    # Auth
    path('signup/', views.signup, name='signup'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),
    path('success/', views.success, name='success'),

    # Bus search & booking
    path('findbus/', views.findbus, name='findbus'),
    path('bookings/', views.bookings, name='bookings'),
    path('reserve-bus/<int:bus_id>/', views.reserve_bus, name='reserve_bus'),

    # My bookings & cancellation
    path('seebookings/', views.seebookings, name='seebookings'),
    path('cancel/', views.cancellings, name='cancellings'),

    # Payment flows
    path('payment/<int:booking_id>/', views.payment_page, name='payment'),
    path('submit-payment/<int:booking_id>/', views.submit_payment, name='submit_payment'),
    path('payment-failed/<int:booking_id>/', views.payment_failed, name='payment_failed'),
]