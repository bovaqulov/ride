from django.contrib import admin
from django.shortcuts import render
from django.urls import path
from django.contrib import messages
import threading
import time
from django.core.cache import cache

from analytics.forms import MassMessageForm
from analytics.telegram_sender import TelegramSender


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
    
    @property
    def urls(self):
        return self.get_urls(), self.name, 'custom_admin'

    # admin site class ichida

    def _send_message_in_background(self, cache_key, message_type, message, parse_mode, custom_ids, media_type, media_file_bytes,
                                    media_filename):
        try:
            sender = TelegramSender()
            results = sender.send_message_by_type(
                message_type=message_type,
                message=message,
                parse_mode=parse_mode,
                custom_ids=custom_ids,
                media_type=media_type,
                media_file_bytes=media_file_bytes,
                media_filename=media_filename,
            )
            total = results.get('success', 0) + results.get('failed', 0) + results.get('blocked', 0)
            cache.set(cache_key, {
                'success': results.get('success', 0),
                'failed': results.get('failed', 0),
                'blocked': results.get('blocked', 0),
                'total': total,
                'status': 'completed',
                'media_type': media_type,
            }, 3600)
        except Exception as e:
            cache.set(cache_key, {
                'success': 0,
                'failed': 0,
                'blocked': 0,
                'total': 0,
                'status': 'error',
                'error': str(e),
            }, 3600)
            print(f"Background xatolik: {e}")

    def send_message_view(self, request):
        """Xabar yuborish sahifasi (optimallashtirilgan)"""
        # Statistikani cache dan olish
        cache_key_stats = "user_stats"
        stats = cache.get(cache_key_stats)

        if not stats:
            try:
                from bot_app.models import BotClient, Driver
                total_drivers = Driver.objects.count()
                total_passengers = BotClient.objects.filter(is_banned=False).count()
                total_banned = BotClient.objects.filter(is_banned=True).count()

                stats = {
                    'total_drivers': total_drivers,
                    'total_passengers': total_passengers,
                    'total_banned': total_banned,
                    'total_users': total_drivers + total_passengers
                }
                cache.set(cache_key_stats, stats, 300)  # 5 minut cache
            except:
                stats = {
                    'total_drivers': 0,
                    'total_passengers': 0,
                    'total_banned': 0,
                    'total_users': 0
                }

        # Message result cache key - stable
        message_result_cache_key = 'last_message_result'
        message_result = cache.get(message_result_cache_key)
        
        if request.method == 'POST':
            form = MassMessageForm(request.POST, request.FILES)
            if form.is_valid():
                message_type = form.cleaned_data['message_type']
                message = form.cleaned_data.get('message', '') or ''
                parse_mode = form.cleaned_data.get('parse_mode', '') or "HTML"
                custom_ids = form.cleaned_data.get('custom_ids', [])
                media_type = form.cleaned_data.get('media_type', 'none')
                media_file = form.cleaned_data.get('media_file')  # InMemoryUploadedFile

                media_file_bytes = None
                media_filename = None
                if media_type != 'none' and media_file:
                    media_file_bytes = media_file.read()
                    media_filename = media_file.name

                # Processing status cache set qilish
                cache.set(message_result_cache_key, {'status': 'processing'}, 3600)
                
                # Background thread ishga tushing
                thread = threading.Thread(
                    target=self._send_message_in_background,
                    args=(message_result_cache_key, message_type, message, parse_mode, custom_ids, media_type, media_file_bytes, media_filename)
                )
                thread.daemon = True
                thread.start()
                
                messages.success(request, "📤 Xabar yuborish jarayoni boshlandi...")

            else:
                form = MassMessageForm()
                # Form errorlarini ko'rsatish
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")

        else:
            form = MassMessageForm()

            # URL dan parameterlarni olish
            telegram_ids = request.GET.get('ids', '')
            message_type_param = request.GET.get('message_type', '')

            if telegram_ids:
                form = MassMessageForm(initial={
                    'message_type': 'custom' if message_type_param else 'all',
                    'custom_ids': ','.join(str(id) for id in telegram_ids.split(','))
                })

        context = self.each_context(request)
        context.update({
            'title': 'Telegram Xabar Yuborish',
            'form': form,
            'total_users': stats['total_users'],
            'total_drivers': stats['total_drivers'],
            'total_passengers': stats['total_passengers'],
            'total_banned': stats['total_banned'],
            'message_result': message_result,
            'opts': self._build_fake_model_options(),
        })

        return render(request, 'admin/send_message.html', context)

    def _build_fake_model_options(self):
        """Admin template lar uchun model options"""

        class FakeMeta:
            app_label = 'analytics'
            model_name = 'send_message'
            verbose_name = 'Xabar Yuborish'
            verbose_name_plural = 'Xabar Yuborish'


        class FakeModel:
            _meta = FakeMeta()

        return FakeModel()._meta

    def get_app_list(self, request, app_label=None):
        """Admin panelda xabar yuborish bo'limini ko'rsatish"""
        app_list = super().get_app_list(request, app_label)

        custom_app = {
            'name': '📢 Xabar Yuborish',
            'app_label': 'telegram_messages',
            'app_url': '/dashboard/send-message/',
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Yangi xabar yuborish',
                    'object_name': 'sendmessage',
                    'admin_url': '/dashboard/send-message/',
                    'view_only': False,
                    'perms': {'add': True, 'change': True, 'delete': True, 'view': True},
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