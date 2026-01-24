from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.contrib import messages
from django.http import HttpResponseRedirect

from analytics.forms import MassMessageForm
from analytics.telegram_sender import TelegramSender
from bot_app.models import Passenger


# CustomAdminSite ni yaratish
class CustomAdminSite(admin.AdminSite):
    site_header = "Taxi Bot Admin"
    site_title = "Taxi Bot Administration"
    index_title = "Boshqaruv paneliga xush kelibsiz"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('send-message/', self.admin_view(self.send_message_view), name='send_message'),
        ]
        return custom_urls + urls

    def send_message_view(self, request):
        """Xabar yuborish sahifasi"""
        if request.method == 'POST':
            form = MassMessageForm(request.POST)
            if form.is_valid():
                sender = TelegramSender()
                message_type = form.cleaned_data['message_type']
                message = form.cleaned_data['message']

                results = {}

                if message_type == 'all':
                    # Hammaga - haydovchi ham, yo'lovchi ham
                    results = sender.send_to_both_groups(message)
                elif message_type == 'users':
                    # Barcha userlarga (driver bo'lsa driver bot orqali)
                    results = sender.send_to_all_users(message)
                elif message_type == 'drivers':
                    # Faqat haydovchilarga
                    results = sender.send_to_all_drivers(message)
                elif message_type == 'passengers':
                    # Faqat yo'lovchilarga
                    results = sender.send_to_all_passengers(message)
                elif message_type == 'banned':
                    from bot_app.models import BotClient
                    banned_users = BotClient.objects.filter(is_banned=True)
                    telegram_ids = list(banned_users.values_list('telegram_id', flat=True))
                    results = sender.send_to_custom_users(telegram_ids, message)
                elif message_type == 'custom':
                    telegram_ids = form.cleaned_data['custom_ids']
                    if telegram_ids:
                        results = sender.send_to_custom_users(telegram_ids, message)

                # Natijani ko'rsatish
                if results.get('success', 0) > 0:
                    messages.success(
                        request,
                        f"✅ {results['success']} ta foydalanuvchiga xabar muvaffaqiyatli yuborildi!"
                    )

                if results.get('failed', 0) > 0:
                    failed_ids = results.get('failed_ids', [])[:10]
                    messages.warning(
                        request,
                        f"⚠️ {results['failed']} ta foydalanuvchiga xabar yuborilmadi. "
                        f"Xatolik yuz bergan ID lar: {failed_ids}"
                    )

                return HttpResponseRedirect('/dashboard')

        else:
            form = MassMessageForm()

            # URL dan telegram_ids parameterini olish
            telegram_ids = request.GET.get('ids', '')
            message_type = request.GET.get('message_type', '')

            if telegram_ids:
                form = MassMessageForm(initial={
                    'message_type': 'custom' if message_type else 'all',
                    'custom_ids': telegram_ids
                })

        # Statistika uchun
        try:
            from bot_app.models import Driver
            total_drivers = Driver.objects.count()
            total_passengers = Passenger.objects.count()
            total_users = total_drivers + total_passengers
        except:
            total_users = 0
            total_drivers = 0
            total_passengers = 0

        context = self.each_context(request)
        context.update({
            'title': 'Telegram Xabar Yuborish',
            'form': form,
            'total_users': total_users,
            'total_drivers': total_drivers,
            'total_passengers': total_passengers,
            'opts': self._build_fake_model_options(),
        })

        return render(request, 'admin/send_message.html', context)

    def _build_fake_model_options(self):
        """Admin template lar uchun model options yaratish"""
        class FakeMeta:
            app_label = 'analytics'
            model_name = 'send_message'
            verbose_name = 'Xabar Yuborish'
            verbose_name_plural = 'Xabar Yuborish'

        class FakeModel:
            _meta = FakeMeta()

        return FakeModel()._meta

    def get_app_list(self, request, app_label=None):
        """
        Admin panelda faqat "Send Telegram Message" bo'limini ko'rsatish
        """
        app_list = super().get_app_list(request, app_label)

        # Faqat "Send Telegram Message" ni ko'rsatish
        custom_app = {
            'name': 'Telegram Xabarlar',
            'app_label': 'telegram_messages',
            'app_url': '/dashboard/send-message/',
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Xabar Yuborish',
                    'object_name': 'sendmessage',
                    'admin_url': '/dashboard/send-message/',
                    'view_only': False,
                    'perms': {
                        'add': True,
                        'change': True,
                        'delete': True,
                        'view': True
                    },
                    'model_name': 'sendmessage',
                    'verbose_name': 'Xabar Yuborish',
                    'verbose_name_plural': 'Xabar Yuborish',
                    'add_url': '/dashboard/send-message/',
                    'count': 1,
                }
            ]
        }

        return [custom_app]


# Custom admin site obyektini yaratish
custom_admin_site = CustomAdminSite(name='custom_admin')