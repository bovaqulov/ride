from django.contrib import admin
from .models import (
    BotClient, PassengerTravel, PassengerPost,
    Driver, Car, DriverTransaction
)


@admin.register(BotClient)
class BotClientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "username", "phone", "language", "is_active", "is_banned", "total_rides", "rating", "created_at")
    list_filter = ("is_active", "is_banned", "language", "created_at")
    search_fields = ("full_name", "username", "phone", "telegram_id")
    list_editable = ("is_active", "is_banned", "rating")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PassengerTravel)
class PassengerTravelAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "from_location", "to_location", "travel_class", "passenger", "price", "has_woman", "status", "created_at")
    list_filter = ("travel_class", "status", "has_woman", "created_at")
    search_fields = ("from_location", "to_location", "user")
    list_editable = ("status", "price", "travel_class")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PassengerPost)
class PassengerPostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "from_location", "to_location", "price", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("from_location", "to_location", "user")
    list_editable = ("price", "status")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


class CarInline(admin.TabularInline):
    model = Car
    extra = 1
    readonly_fields = ("created_at", "updated_at")


class DriverTransactionInline(admin.TabularInline):
    model = DriverTransaction
    extra = 1
    readonly_fields = ("created_at",)


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "from_location", "to_location", "status", "amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("user", "from_location", "to_location")
    list_editable = ("status", "amount")
    inlines = [CarInline, DriverTransactionInline]
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


# @admin.register(Car)
# class CarAdmin(admin.ModelAdmin):
#     list_display = ("id", "driver", "car_number", "car_model", "car_color", "created_at")
#     search_fields = ("car_number", "car_model", "driver__user")
#     list_filter = ("car_color", "created_at")
#     readonly_fields = ("created_at", "updated_at")
#     ordering = ("-created_at",)
#
#
# @admin.register(DriverTransaction)
# class DriverTransactionAdmin(admin.ModelAdmin):
#     list_display = ("id", "driver", "amount", "created_at")
#     search_fields = ("driver__user",)
#     list_filter = ("created_at",)
#     readonly_fields = ("created_at",)
#     ordering = ("-created_at",)
