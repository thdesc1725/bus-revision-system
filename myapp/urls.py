from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('findbus', views.findbus, name="findbus"),
    path('bookings', views.bookings, name="bookings"),
    path('cancellings', views.cancellings, name="cancellings"),
    path('seebookings', views.seebookings, name="seebookings"),
    path('signup', views.signup, name="signup"),
    path('signin', views.signin, name="signin"),
    path('success', views.success, name="success"),
    path('signout', views.signout, name="signout"),

    # payment urls
    path('payment/<int:booking_id>/', views.payment_page, name='payment'),
    path('payment-success/<int:booking_id>/', views.payment_success, name='payment_success'),
    path('payment-failed/<int:booking_id>/', views.payment_failed, name='payment_failed'),
]