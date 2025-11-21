# bot_app/admin.py

from django.contrib import admin
from .models import BotClient, PassengerPost


@admin.register(BotClient)
class BotClientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "telegram_id", "username", "phone", "language", "is_active", "is_banned", "rating", "total_rides", "created_at")
    list_filter = ("is_active", "is_banned", "language", "rating")
    search_fields = ("full_name", "username", "phone", "telegram_id")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("is_active", "is_banned", "rating")
    date_hierarchy = "created_at"


# PassengerPost modelining ma'muriy interfeysini moslashtirish
@admin.register(PassengerPost)
class PassengerPostAdmin(admin.ModelAdmin):
    # Ma'muriyat ro'yxat sahifasida ko'rsatiladigan maydonlar (ustunlar)
    list_display = ('id', 'user', 'from_location', 'to_location', 'price', 'status', 'created_at')

    # Filtrlash yoqiladigan maydonlar (yon paneldagi filtrlar)
    list_filter = ('status', 'created_at', 'updated_at')

    # Qidirish yoqiladigan maydonlar (yuqoridagi qidiruv paneli)
    search_fields = ('from_location', 'to_location', 'user')

    # Sana va vaqt maydonlarini navigatsiya qilish uchun sozlash
    date_hierarchy = 'created_at'

    # Ro'yxatdan turib tahrirlashga ruxsat beriladigan maydonlar (ular list_displayda bo'lishi kerak)
    list_editable = ('status', 'price')

    # Ro'yxatdagi har bir sahifada ko'rsatiladigan elementlar soni
    list_per_page = 20