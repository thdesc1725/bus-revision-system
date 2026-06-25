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


class Book(models.Model):
    # Ticket status
    PENDING = 'PENDING'
    CONFIRMED = 'CONFIRMED'
    CANCELLED = 'CANCELLED'

    TICKET_STATUSES = (
        (PENDING, 'Pending'),
        (CONFIRMED, 'Confirmed'),
        (CANCELLED, 'Cancelled'),
    )

    # Payment status
    PAYMENT_PENDING = 'PENDING'
    PAYMENT_PENDING_VERIFICATION = 'PENDING_VERIFICATION'
    PAYMENT_PAID = 'PAID'
    PAYMENT_FAILED = 'FAILED'
    PAYMENT_REFUNDED = 'REFUNDED'

    PAYMENT_STATUSES = (
        (PAYMENT_PENDING, 'Pending'),
        (PAYMENT_PENDING_VERIFICATION, 'Pending Verification'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_FAILED, 'Failed'),
        (PAYMENT_REFUNDED, 'Refunded'),
    )

    email = models.EmailField()
    name = models.CharField(max_length=30)
    userid = models.IntegerField()
    busid = models.IntegerField()
    bus_name = models.CharField(max_length=30)
    source = models.CharField(max_length=30)
    dest = models.CharField(max_length=30)
    nos = models.IntegerField()
    price = models.DecimalField(decimal_places=2, max_digits=10)
    total_price = models.DecimalField(decimal_places=2, max_digits=10, default=0)
    date = models.DateField()
    time = models.TimeField()

    status = models.CharField(max_length=20, choices=TICKET_STATUSES, default=PENDING)

    payment_status = models.CharField(
        max_length=30,
        choices=PAYMENT_STATUSES,
        default=PAYMENT_PENDING
    )

    payment_id = models.CharField(max_length=100, blank=True, null=True)

    payment_screenshot = models.ImageField(upload_to='payments/', blank=True, null=True)
    upi_reference = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.bus_name} - {self.status}"