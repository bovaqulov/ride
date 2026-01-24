
from typing import List, Dict
import concurrent.futures
from django.db import connection

from bot_app.models import BotClient, Driver
from configuration import env


class TelegramSender:
    def __init__(self):
        self.passenger_bot_token = env.PASSENGER_BOT_TOKEN
        self.driver_bot_token = env.DRIVER_BOT_TOKEN
        self.base_url = "https://api.telegram.org/bot"

    def _send_single_message(self, chat_id: int, message: str,
                             parse_mode: str = "HTML", is_driver: bool = False) -> bool:
        """Bir dona xabarni yuborish (sync)"""
        import requests
        import json

        token = self.driver_bot_token if is_driver else self.passenger_bot_token
        url = f"{self.base_url}{token}/sendMessage"

        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': parse_mode,
            'disable_web_page_preview': True
        }

        try:
            # Timeout bilan ishlash
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                result = response.json()
                return result.get('ok', False)
            return False
        except Exception:
            return False

    def _send_batch_messages(self, batch_data: List[Dict], message: str,
                             parse_mode: str = "HTML") -> Dict:
        """Bir batch uchun xabarlarni yuborish (parallel)"""
        results = {
            'success': 0,
            'failed': 0,
            'failed_ids': []
        }

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Vazifalarni yaratish
            future_to_id = {}
            for data in batch_data:
                telegram_id = data['id']
                is_driver = data.get('is_driver', False)
                future = executor.submit(
                    self._send_single_message,
                    telegram_id, message, parse_mode, is_driver
                )
                future_to_id[future] = telegram_id

            # Natijalarni olish
            for future in concurrent.futures.as_completed(future_to_id):
                telegram_id = future_to_id[future]
                try:
                    success = future.result(timeout=6)
                    if success:
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                        results['failed_ids'].append(telegram_id)
                except Exception:
                    results['failed'] += 1
                    results['failed_ids'].append(telegram_id)

        return results

    def send_bulk(self, telegram_data: List[Dict], message: str,
                  parse_mode: str = "HTML", batch_size: int = 100) -> Dict:
        """Bulk xabar yuborish (optimallashtirilgan)"""
        results = {
            'success': 0,
            'failed': 0,
            'failed_ids': []
        }

        # Ma'lumotlarni batchlarga bo'lish
        for i in range(0, len(telegram_data), batch_size):
            batch = telegram_data[i:i + batch_size]
            batch_results = self._send_batch_messages(batch, message, parse_mode)

            results['success'] += batch_results['success']
            results['failed'] += batch_results['failed']
            results['failed_ids'].extend(batch_results['failed_ids'])

            # Har bir batchdan keyin connection ni yopish
            connection.close()

        return results

    def get_all_users_data_fast(self) -> List[Dict]:
        """Barcha foydalanuvchilar uchun telegram ma'lumotlarini tez olish"""
        users_data = []

        # Barcha driver ID larni bir martada olish
        driver_ids = set(Driver.objects.filter(telegram_id__isnull=False)
                         .values_list('telegram_id', flat=True))

        # BotClient lardan foydalanuvchilarni olish
        users = BotClient.objects.filter(
            is_banned=False,
            telegram_id__isnull=False
        ).only('telegram_id').iterator(chunk_size=1000)

        for user in users:
            users_data.append({
                'id': user.telegram_id,
                'is_driver': user.telegram_id in driver_ids
            })

        return users_data

    def get_only_passengers_data(self) -> List[Dict]:
        """Faqat yo'lovchilar uchun ma'lumot olish"""
        users_data = []

        # Driver ID larni olish
        driver_ids = set(Driver.objects.filter(telegram_id__isnull=False)
                         .values_list('telegram_id', flat=True))

        # Faqat yo'lovchi bo'lganlar
        passengers = BotClient.objects.filter(
            is_banned=False,
            telegram_id__isnull=False
        ).exclude(telegram_id__in=driver_ids).only('telegram_id').iterator(chunk_size=1000)

        for passenger in passengers:
            users_data.append({
                'id': passenger.telegram_id,
                'is_driver': False
            })

        return users_data

    def get_only_drivers_data(self) -> List[Dict]:
        """Faqat haydovchilar uchun ma'lumot olish"""
        drivers_data = []

        drivers = Driver.objects.filter(
            telegram_id__isnull=False
        ).only('telegram_id').iterator(chunk_size=1000)

        for driver in drivers:
            drivers_data.append({
                'id': driver.telegram_id,
                'is_driver': True
            })

        return drivers_data

    def get_banned_users_data(self) -> List[Dict]:
        """Bloklangan foydalanuvchilar uchun ma'lumot olish"""
        users_data = []

        banned_users = BotClient.objects.filter(
            is_banned=True,
            telegram_id__isnull=False
        ).only('telegram_id').iterator(chunk_size=1000)

        # Driver ID larni olish
        driver_ids = set(Driver.objects.filter(telegram_id__isnull=False)
                         .values_list('telegram_id', flat=True))

        for user in banned_users:
            users_data.append({
                'id': user.telegram_id,
                'is_driver': user.telegram_id in driver_ids
            })

        return users_data

    def get_custom_users_data(self, telegram_ids: List[int]) -> List[Dict]:
        """Custom ID lar uchun ma'lumot olish"""
        if not telegram_ids:
            return []

        users_data = []

        # Driver ID larni olish
        driver_ids = set(Driver.objects.filter(telegram_id__isnull=False)
                         .values_list('telegram_id', flat=True))

        for telegram_id in telegram_ids:
            users_data.append({
                'id': telegram_id,
                'is_driver': telegram_id in driver_ids
            })

        return users_data

    def send_message_by_type(self, message_type: str, message: str,
                             parse_mode: str = "HTML", custom_ids: List[int] = None) -> Dict:
        """Xabar turi bo'yicha yuborish"""
        # Ma'lumotlarni olish
        if message_type == 'all':
            telegram_data = self.get_all_users_data_fast()
        elif message_type == 'users':
            telegram_data = self.get_only_passengers_data()
        elif message_type == 'drivers':
            telegram_data = self.get_only_drivers_data()
        elif message_type == 'banned':
            telegram_data = self.get_banned_users_data()
        elif message_type == 'custom' and custom_ids:
            telegram_data = self.get_custom_users_data(custom_ids)
        else:
            return {'success': 0, 'failed': 0, 'failed_ids': []}

        # Xabarni yuborish
        if telegram_data:
            return self.send_bulk(telegram_data, message, parse_mode)
        else:
            return {'success': 0, 'failed': 0, 'failed_ids': []}