from django.db import models


class Bus(models.Model):
    bus_name = models.CharField(max_length=30)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    nos = models.DecimalField(decimal_places=0, max_digits=5)
    rem = models.DecimalField(decimal_places=0, max_digits=5)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    date = models.DateField()
    time = models.TimeField()

    def __str__(self):
        return self.bus_name


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField()
    name = models.CharField(max_length=30)
    password = models.CharField(max_length=30)

    def __str__(self):
        return self.email


class Book(models.Model):
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'

    TICKET_STATUSES = (
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    )

    email = models.EmailField()
    name = models.CharField(max_length=30)
    userid = models.IntegerField()
    busid = models.IntegerField()
    bus_name = models.CharField(max_length=30)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    nos = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=10)   # price per seat
    total_price = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    date = models.DateField()
    time = models.TimeField()
    status = models.CharField(choices=TICKET_STATUSES, default=PENDING, max_length=20)

    # payment fields
    payment_status = models.CharField(max_length=20, default='PENDING')
    payment_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.bus_name} - {self.status}"