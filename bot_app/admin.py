
from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe

from .models import (
    BotClient, PassengerTravel, PassengerPost,
    Driver, Car, DriverTransaction, City, Order, Passenger, DriverGallery, CityPrice, Route, Tariff, RouteCashback
)

admin.site.site_header = "Taxi Bot Admin"
admin.site.site_title = "Taxi Bot Administration"
admin.site.index_title = "Boshqaruv paneliga xush kelibsiz"

@admin.register(BotClient)
class BotClientAdmin(admin.ModelAdmin):
    list_display = ("new_full_name", "username", "language", "is_banned")
    list_filter = ("is_banned", "language", "created_at")
    search_fields = ("full_name", "username", "telegram_id")
    list_editable = ("is_banned",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


    def new_full_name(self, obj):
        return f"{obj.full_name}({obj.telegram_id})"

    new_full_name.short_description = "Ism"

@admin.register(PassengerTravel)
class PassengerTravelAdmin(admin.ModelAdmin):
    list_display = [
        'get_creator_name',
        'get_start_time',
        'get_locations',
        'passenger',
        'has_woman',
        'comment',
    ]

    list_filter = [ 'has_woman', 'created_at']
    search_fields = ['user', ]
    readonly_fields = ['created_at',]

    # start_time uchun custom metod
    def get_start_time(self, obj):
        if obj.start_time:
            try:
                # timezone aware bo'lsa
                from django.utils import timezone
                if timezone.is_aware(obj.start_time):
                    return timezone.localtime(obj.start_time).strftime("%Y-%m-%d %H:%M")
                return obj.start_time.strftime("%Y-%m-%d %H:%M")
            except (AttributeError, ValueError):
                return "Xato"
        return "Belgilanmagan"

    get_start_time.short_description = "Boshlanish vaqti"
    get_start_time.admin_order_field = 'start_time'

    def get_creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except (BotClient.DoesNotExist, ImportError):
            return str(obj.user)

    get_creator_name.short_description = "Sayohatchi egasi"

    def get_locations(self, obj):
        try:
            # JSON fielddan ma'lumot olish
            from_location = obj.from_location
            to_location = obj.to_location

            # Agar dict bo'lsa
            if isinstance(from_location, dict) and isinstance(to_location, dict):
                from_city = from_location.get('city', '')
                to_city = to_location.get('city', '')
                return f"{from_city} → {to_city}"

            # Agar string bo'lsa
            return f"{from_location} → {to_location}"
        except Exception as e:
            return f"Xato: {str(e)}"

    get_locations.short_description = "Yo'nalish"

    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('user', 'start_time', 'comment')
        }),
        ("Lokatsiyalar", {
            'fields': ('from_location', 'to_location')
        }),
        ("Vaqt belgilari", {
            'fields': ('created_at',)
        }),
    )

@admin.register(PassengerPost)
class PassengerPostAdmin(admin.ModelAdmin):
    list_display = ("id", "creator_name", "comment", "get_start_time", "get_locations", "created_at")
    search_fields = ("user", "comment")
    ordering = ("-created_at",)
    list_filter = ("start_time",)  # Agar start_time None bo'lsa, bu filterda muammo bo'lishi mumkin

    readonly_fields = ('created_at',)  # <-- bu yerga qo'shildi

    # start_time uchun custom metod
    def get_start_time(self, obj):
        if obj.start_time:
            try:
                from django.utils import timezone
                if timezone.is_aware(obj.start_time):
                    return timezone.localtime(obj.start_time).strftime("%Y-%m-%d %H:%M")
                return obj.start_time.strftime("%Y-%m-%d %H:%M")
            except (AttributeError, ValueError):
                return "Xato"
        return "Belgilanmagan"

    get_start_time.short_description = "Boshlanish vaqti"
    get_start_time.admin_order_field = 'start_time'

    def creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except (BotClient.DoesNotExist, ImportError):
            return str(obj.user)

    creator_name.short_description = "Pochta egasi"

    def get_locations(self, obj):
        try:
            from_location = obj.from_location
            to_location = obj.to_location

            if isinstance(from_location, dict) and isinstance(to_location, dict):
                from_city = from_location.get('city', '')
                to_city = to_location.get('city', '')
                return f"{from_city} → {to_city}"

            return f"{from_location} → {to_location}"
        except Exception as e:
            return f"Xato: {str(e)}"

    get_locations.short_description = "Yo'nalish"

    # Admin change form uchun
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            'fields': ('user', 'start_time', 'comment')
        }),
        ("Lokatsiyalar", {
            'fields': ('from_location', 'to_location')
        }),
        ("Vaqt belgilari", {
            'fields': ('created_at',)  # endi readonly_fields bilan muammo bo'lmaydi
        }),
    )

class CarInline(admin.TabularInline):
    model = Car
    extra = 1
    readonly_fields = ("created_at", "updated_at")
    fields = ('car_number', 'car_model', 'car_color', 'tariff', 'created_at', 'updated_at')


class DriverTransactionInline(admin.TabularInline):
    model = DriverTransaction
    extra = 1
    readonly_fields = ("created_at",)


class DriverGalleryInline(admin.StackedInline):
    model = DriverGallery
    can_delete = False
    extra = 0
    max_num = 1


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Asosiy ma'lumotlar", {
            "fields": ("telegram_id", "full_name", "phone", "rating", "last_online_at")
        }),
        ("Holat va joylashuv", {
            "fields": ("status", "amount", "route_id", "from_location", "to_location")
        }),
        ("Vaqtlar", {
            "fields": ("created_at", "updated_at")
        }),
    )

    readonly_fields = ("created_at", "updated_at")

    list_display = (
        "new_full_name",
        "car_info",
        "phone",
        "status",
        "route_id",
        "amount",
    )
    list_editable = ("amount", "status", "route_id")
    list_filter = ("status", "route_id", "from_location", "to_location")
    search_fields = ("telegram_id", "phone", "full_name")
    inlines = (DriverGalleryInline, CarInline, DriverTransactionInline)
    ordering = ("-created_at",)

    def save_model(self, request, obj, form, change):
        # Yangi driver yaratilganda last_online_at ni to'ldirish
        if not change:
            obj.last_online_at = timezone.now()
        super().save_model(request, obj, form, change)

    def new_full_name(self, obj):
        return f"{obj.full_name} ({obj.telegram_id})"

    new_full_name.short_description = "Ism"

    def car_info(self, obj):
        try:
            # Car modelidagi driver ForeignKey nomi 'driver' deb qoldi
            car = Car.objects.filter(driver=obj).first()
            if car:
                tariff_info = f" ({car.tariff})" if car.tariff else ""
                return mark_safe(f"<b>{car.car_model} ({car.car_number}){tariff_info}</b>")
        except Exception:
            return ""
        return ""

    car_info.short_description = mark_safe("<b>Avtomobil</b>")

    def formatted_last_online(self, obj):
        if obj.last_online_at:
            dt = obj.last_online_at
            if timezone.is_aware(dt):
                dt = timezone.localtime(dt)
            return dt.strftime("%Y-%m-%d %H:%M")
        return "N/A"

    formatted_last_online.short_description = "Online vaqti"
    formatted_last_online.admin_order_field = "last_online_at"

    # Custom action: tanlangan driverlarning last_online_at ni yangilash
    actions = ['update_last_online_to_now']

    def update_last_online_to_now(self, request, queryset):
        updated_count = queryset.update(last_online_at=timezone.now())
        self.message_user(request, f"{updated_count} ta driverning online vaqti yangilandi.")

    update_last_online_to_now.short_description = "Online vaqtini hozirgi vaqtga yangilash"


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    # Ro'yxat ko'rinishi
    list_display = ['id', 'title', 'get_subcategory', 'is_allowed', 'created_at']
    list_filter = ['is_allowed', 'created_at']
    search_fields = ['title']

    fields = [
        'title',
        'subcategory',
        'latitude',
        'longitude',
        'translate',
        'is_allowed'
    ]


    # Qo'shimcha funksiyalar
    def get_subcategory(self, obj):
        return obj.subcategory.title if obj.subcategory else "-"

    get_subcategory.short_description = "Subkategoriya"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Ro'yxatda ko'rsatiladigan maydonlar
    list_display = [
        'id',
        'creator_name',
        'order_type',
        'status',
        'driver'
    ]

    # Filter panel
    list_filter = [
        'user',
        'status',
        'driver'
    ]

    # Qidiruv maydonlari
    search_fields = [
        'user',
        'driver__full_name',
        'driver__phone',

    ]
    list_editable = ["status", "driver"]

    # Readonly maydonlar
    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    # Sahifadagi elementlar soni
    list_per_page = 20

    # Sana bo'yicha guruhlash
    date_hierarchy = 'created_at'


    # Actionlar
    actions = ['make_ended', 'make_rejected']

    def make_ended(self, request, queryset):
        """Tanlangan orderlarni completed qilish"""
        updated = queryset.update(status='ended')
        self.message_user(request, f'{updated} ta order completed holatiga o\'zgartirildi')

    make_ended.short_description = "Tanlangan orderlarni completed qilish"

    def make_rejected(self, request, queryset):
        """Tanlangan orderlarni cancelled qilish"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} ta order cancelled holatiga o\'zgartirildi')

    make_rejected.short_description = "Tanlangan orderlarni cancelled qilish"

    def creator_name(self, obj):
        try:
            client = BotClient.objects.get(telegram_id=obj.user)
            return f"{client.full_name}({obj.user})"
        except BotClient.DoesNotExist:
            return obj.user

    creator_name.short_description = "buyurtma egasi"

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):

    # Ro'yxat ko'rinishidagi ustunlar
    list_display = [
        'id',
        'telegram_id',
        'full_name',
        'phone',
        'total_rides',
        'rating',
        'created_at'
    ]

    # Filtrlar
    list_filter = [
        'rating',
        'created_at',
        'updated_at'
    ]

    # Qidiruv maydonlari
    search_fields = [
        'telegram_id',
        'full_name',
        'phone'
    ]

    # Tartiblash
    ordering = ['-rating']

    # Faqat o'qish uchun maydonlar
    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    # Maydonlar guruhlari
    fieldsets = (
        ('Asosiy maʼlumotlar', {
            'fields': (
                'telegram_id',
                'full_name',
                'phone'
            )
        }),
        ('Statistika', {
            'fields': (
                'total_rides',
                'rating'
            )
        }),
        ('Qo\'shimcha maʼlumotlar', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)  # Yig'iladigan blok
        }),
    )

    # Admin panelda ko'rsatiladigan sarlavha
    list_display_links = ['telegram_id', 'full_name']

    # Sahifadagi elementlar soni
    list_per_page = 20

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['telegram_id', 'created_at', 'updated_at']
        else:  # yangi yaratish
            return ['created_at', 'updated_at']

@admin.register(Tariff)
class TariffInline(admin.ModelAdmin):
    list_display = ('id', 'title', 'is_active')

@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    class CityPriceAdmin(admin.TabularInline):
        model = CityPrice
        extra = 1

    class RouteCashbackInline(admin.TabularInline):
        model = RouteCashback
        extra = 1

    list_display = ('id', "from_city", "to_city", 'is_active')
    inlines = [CityPriceAdmin, RouteCashbackInline]