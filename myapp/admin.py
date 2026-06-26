import os
from django.contrib import admin, messages
from django.utils.html import format_html
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction

from .models import Bus, Book


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ('id', 'bus_name', 'source', 'dest', 'date', 'time', 'nos', 'rem', 'price')
    search_fields = ('bus_name', 'source', 'dest')
    list_filter = ('date', 'source', 'dest')


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'email',
        'bus_name',
        'source',
        'dest',
        'date',
        'time',
        'nos',
        'total_price',
        'status',
        'payment_status',
        'upi_reference',
        'payment_proof_preview',
    )

    list_filter = ('status', 'payment_status', 'date', 'source', 'dest')
    search_fields = ('name', 'email', 'bus_name', 'upi_reference')
    readonly_fields = (
        'payment_proof_preview_large',
        'booking_summary',
    )

    fieldsets = (
        ('User / Booking Info', {
            'fields': (
                'name', 'email', 'userid',
                'busid', 'bus_name',
                'source', 'dest',
                'date', 'time',
                'nos', 'price', 'total_price',
                'booking_summary',
            )
        }),
        ('Payment Info', {
            'fields': (
                'payment_status',
                'payment_id',
                'upi_reference',
                'payment_screenshot',
                'payment_proof_preview_large',
            )
        }),
        ('Ticket Status', {
            'fields': ('status',)
        }),
    )

    actions = ['approve_payment', 'reject_payment']

    def booking_summary(self, obj):
        return format_html(
            "<b>Booking ID:</b> {}<br>"
            "<b>Passenger:</b> {}<br>"
            "<b>Bus:</b> {}<br>"
            "<b>Route:</b> {} → {}<br>"
            "<b>Date:</b> {}<br>"
            "<b>Time:</b> {}<br>"
            "<b>Seats:</b> {}<br>"
            "<b>Total:</b> ₹ {}<br>"
            "<b>Ticket Status:</b> {}<br>"
            "<b>Payment Status:</b> {}",
            obj.id,
            obj.name,
            obj.bus_name,
            obj.source,
            obj.dest,
            obj.date,
            obj.time,
            obj.nos,
            obj.total_price,
            obj.status,
            obj.payment_status,
        )
    booking_summary.short_description = "Booking Summary"

    def payment_proof_preview(self, obj):
        if obj.payment_screenshot:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" width="70" height="70" style="border-radius:8px; object-fit:cover;" />'
                '</a>',
                obj.payment_screenshot.url,
                obj.payment_screenshot.url
            )
        return "No Screenshot"
    payment_proof_preview.short_description = "Payment Proof"

    def payment_proof_preview_large(self, obj):
        if obj.payment_screenshot:
            return format_html(
                '<a href="{0}" target="_blank">'
                '<img src="{0}" width="300" style="border:1px solid #ddd; border-radius:10px; padding:4px;" />'
                '</a>',
                obj.payment_screenshot.url
            )
        return "No screenshot uploaded"
    payment_proof_preview_large.short_description = "Uploaded Screenshot"

    def approve_payment(self, request, queryset):
        approved_count = 0

        # Run inside an atomic block to prevent seat calculation discrepancies
        with transaction.atomic():
            for book in queryset:
                if book.status == 'CONFIRMED':
                    continue

                if book.payment_status != 'PENDING_VERIFICATION':
                    self.message_user(
                        request,
                        f"Booking #{book.id} cannot be approved because payment proof is not submitted.",
                        level=messages.WARNING
                    )
                    return

                try:
                    # Target single bus inventory line row using select_for_update to handle race conditions
                    bus = Bus.objects.select_for_update().get(id=book.busid)
                except Bus.DoesNotExist:
                    self.message_user(
                        request,
                        f"Bus not found for booking #{book.id}",
                        level=messages.ERROR
                    )
                    return

                if int(bus.rem) < int(book.nos):
                    book.status = 'CANCELLED'
                    book.payment_status = 'FAILED'
                    book.save()

                    self.message_user(
                        request,
                        f"Booking #{book.id} automatically cancelled: Insufficient remaining seats available.",
                        level=messages.WARNING
                    )
                    return

                # Safely deduct ticket count from active tracking total
                bus.rem = int(bus.rem) - int(book.nos)
                bus.save()

                book.status = 'CONFIRMED'
                book.payment_status = 'PAID'

                if not book.payment_id:
                    book.payment_id = f"PAY{book.id}{book.userid}"

                book.save()

                # Dispatch asynchronous email payloads
                subject = "Bus Ticket Confirmed"
                message = f"""
Hello {book.name},

Your bus ticket has been CONFIRMED successfully.

Ticket Details:
Booking ID: {book.id}
Bus Name: {book.bus_name}
From: {book.source}
To: {book.dest}
Journey Date: {book.date}
Journey Time: {book.time}
Number of Seats: {book.nos}
Price per Seat: ₹{book.price}
Total Price: ₹{book.total_price}

Ticket Status: {book.status}
Payment Status: {book.payment_status}
Payment ID: {book.payment_id}

Thank you for booking with us.
"""
                try:
                    send_mail(
                        subject,
                        message,
                        settings.DEFAULT_FROM_EMAIL,
                        [book.email],
                        fail_silently=False,
                    )
                except Exception as e:
                    self.message_user(
                        request,
                        f"Booking #{book.id} approved, but confirmation email failed to transmit: {str(e)}",
                        level=messages.WARNING
                    )

                approved_count += 1

        if approved_count > 0:
            self.message_user(
                request,
                f"{approved_count} booking(s) approved successfully and seats assigned.",
                level=messages.SUCCESS
            )

    approve_payment.short_description = "Approve selected payment(s)"

    def reject_payment(self, request, queryset):
        updated = 0

        with transaction.atomic():
            for book in queryset:
                if book.status == 'CONFIRMED':
                    continue

                book.payment_status = 'FAILED'
                book.status = 'CANCELLED'
                book.save()
                updated += 1

        if updated > 0:
            self.message_user(
                request,
                f"{updated} booking(s) rejected/cancelled successfully.",
                level=messages.SUCCESS
            )

    reject_payment.short_description = "Reject selected payment(s)"