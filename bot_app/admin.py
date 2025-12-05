from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BotClient, PassengerTravel, PassengerPost,
    Driver, Car, DriverTransaction, City, Order, Passenger, DriverGallery
)


@admin.register(BotClient)
class BotClientAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "username", "language", "is_banned", "created_at")
    list_filter = ("is_banned", "language", "created_at")
    search_fields = ("full_name", "username", "telegram_id")
    list_editable = ("is_banned",)
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(PassengerTravel)
class PassengerTravelAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'user',
        'rate',
        'price',
        'created_at'
    ]

    list_filter = ['travel_class', 'has_woman', 'created_at']
    search_fields = ['user', ]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PassengerPost)
class PassengerPostAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "from_location", "to_location", "price", "created_at")
    list_filter = ("created_at",)
    search_fields = ("from_location", "to_location", "user")
    list_editable = ("price",)
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

class DriverGalleryInline(admin.StackedInline):
    """DriverGallery modelini Driver adminida inline ko'rinishda ko'rsatish"""
    model = DriverGallery
    can_delete = False
    extra = 0
    max_num = 1


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ("id", "telegram_id", "from_location", "to_location", "amount", "created_at")
    list_filter = ("created_at",)
    search_fields = ("telegram_id", "from_location", "to_location")
    list_editable = ("amount",)
    inlines = [DriverGalleryInline, CarInline, DriverTransactionInline]
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


class CityPriceInline(admin.TabularInline):
    model = City
    extra = 1

class CityAdmin(admin.ModelAdmin):
    list_display = [
        'title',
        'subcategory',
        'is_allowed',
        'created_at',
        'updated_at',
        'actions_column'
    ]
    inlines = [CityPriceInline]
    list_filter = [
        'is_allowed',
        'subcategory',
        'created_at',
        'updated_at'
    ]
    search_fields = [
        'title',
        'subcategory__title'
    ]
    list_per_page = 20
    list_select_related = ['subcategory']
    actions = ['make_allowed', 'make_not_allowed']
    readonly_fields = ['created_at', 'updated_at', 'subcategory_tree']
    fieldsets = (
        ('Asosiy maʼlumotlar', {
            'fields': ('title', 'translate', "latitude", "longitude", 'subcategory', 'is_allowed')
        }),
        ('Qoʻshimcha maʼlumotlar', {
            'fields': ('subcategory_tree', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('subcategory')

    def subcategory_tree(self, obj):
        """Subkategoriya daraxtini ko'rsatish"""
        if not obj.subcategory:
            return "Asosiy kategoriya"

        tree = []
        current = obj.subcategory
        while current:
            tree.append(current.title)
            current = current.subcategory

        return " → ".join(reversed(tree))

    subcategory_tree.short_description = "Subkategoriya daraxti"

    def actions_column(self, obj):
        """Amallar ustuni"""
        allowed_text = "✅ Ruxsat etilgan" if obj.is_allowed else "❌ Ruxsat etilmagan"
        return format_html(
            '<span style="font-size: 12px;">{}</span>',
            allowed_text
        )

    actions_column.short_description = "Holati"
    actions_column.admin_order_field = 'is_allowed'

    def make_allowed(self, request, queryset):
        """Tanlangan shaharlarni ruxsat etilgan qilish"""
        updated = queryset.update(is_allowed=True)
        self.message_user(
            request,
            f"{updated} ta shahar ruxsat etilgan qilindi."
        )

    make_allowed.short_description = "Tanlangan shaharlarni ruxsat etilgan qilish"

    def make_not_allowed(self, request, queryset):
        """Tanlangan shaharlarni ruxsat etilmagan qilish"""
        updated = queryset.update(is_allowed=False)
        self.message_user(
            request,
            f"{updated} ta shahar ruxsat etilmagan qilindi."
        )

    make_not_allowed.short_description = "Tanlangan shaharlarni ruxsat etilmagan qilish"

    def get_list_display(self, request):
        """Foydalanuvchi huquqlariga qarab list display ni sozlash"""
        base_list_display = list(self.list_display)
        if request.user.is_superuser:
            return base_list_display
        return [field for field in base_list_display if field != 'actions_column']

    def get_fieldsets(self, request, obj=None):
        """Foydalanuvchi huquqlariga qarab fieldsets ni sozlash"""
        if request.user.is_superuser:
            return self.fieldsets
        else:
            return (
                ('Asosiy maʼlumotlar', {
                    'fields': ('title', 'subcategory', "latitude", "longitude", 'is_allowed')
                }),
            )

    def save_model(self, request, obj, form, change):
        """Modelni saqlashda qo'shimcha tekshirishlar"""
        if obj.subcategory and obj.subcategory == obj:
            from django.core.exceptions import ValidationError
            raise ValidationError("Shahar o'zining subkategoriyasi bo'la olmaydi")

        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Subcategory uchun foreign key sozlamalari"""
        if db_field.name == "subcategory":
            # O'zini o'ziga bog'lashni oldini olish
            if hasattr(request, '_obj') and request._obj:
                kwargs["queryset"] = City.objects.exclude(id=request._obj.id)
            else:
                kwargs["queryset"] = City.objects.all()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        """Formani o'zgartirish"""
        if obj:
            request._obj = obj
        return super().get_form(request, obj, **kwargs)


class CitySubcategoryInline(admin.TabularInline):
    """City uchun subcategory inline"""
    model = City
    fk_name = 'subcategory'
    extra = 0
    fields = ['title', 'is_allowed', 'created_at']
    readonly_fields = ['created_at']
    can_delete = False
    show_change_link = True

    def has_add_permission(self, request, obj):
        """Qo'shish huquqini cheklash"""
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        """O'zgartirish huquqini cheklash"""
        return request.user.is_superuser


class CityAdminWithInline(CityAdmin):
    """Inline bilan kengaytirilgan admin"""
    inlines = [CitySubcategoryInline]

    def get_inline_instances(self, request, obj=None):
        """Faqlg obj mavjud bo'lganda inline larni ko'rsatish"""
        if obj:
            return super().get_inline_instances(request, obj)
        return []


# Admin ga ro'yxatdan o'tkazish
admin.site.register(City, CityAdminWithInline)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    # Ro'yxatda ko'rsatiladigan maydonlar
    list_display = [
        'id',
        'user',
        'order_type',
        'status',
        'driver',
        'content_type',
        'object_id',
        'created_at'
    ]

    # Filter panel
    list_filter = [
        'status',
        'order_type',
        'created_at',
        'driver'
    ]

    # Qidiruv maydonlari
    search_fields = [
        'user',
        'driver__name',
        'driver__phone'
    ]

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
    actions = ['make_completed', 'make_cancelled']

    def make_completed(self, request, queryset):
        """Tanlangan orderlarni completed qilish"""
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} ta order completed holatiga o\'zgartirildi')

    make_completed.short_description = "Tanlangan orderlarni completed qilish"

    def make_cancelled(self, request, queryset):
        """Tanlangan orderlarni cancelled qilish"""
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} ta order cancelled holatiga o\'zgartirildi')

    make_cancelled.short_description = "Tanlangan orderlarni cancelled qilish"


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
        """Yangi yaratishda telegram_id ni o'zgartirish mumkin, mavjud bo'lsa yo'q"""
        if obj:  # object mavjud bo'lsa (yangilash)
            return ['telegram_id', 'created_at', 'updated_at']
        else:  # yangi yaratish
            return ['created_at', 'updated_at']

