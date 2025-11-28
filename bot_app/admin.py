from django.contrib import admin
from django.utils.html import format_html

from .models import (
    BotClient, PassengerTravel, PassengerPost,
    Driver, Car, DriverTransaction, City
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
    list_display = ("id", "telegram_id", "from_location", "to_location", "status", "amount", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("telegram_id", "from_location", "to_location")
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




class CityAdmin(admin.ModelAdmin):

    list_display = [
        'title',
        'subcategory',
        'is_allowed',
        'created_at',
        'updated_at',
        'actions_column'
    ]
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
            'fields': ('title', 'translate', 'subcategory', 'is_allowed')
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

# Yoki oddiy versiyani ishlatish uchun:
# admin.site.register(City, CityAdmin)
