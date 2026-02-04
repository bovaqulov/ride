import io
import time
from typing import List, Dict
import concurrent.futures

from telebot import TeleBot
from django.db import connection

from bot_app.models import BotClient, Driver
from configuration import env


class TelegramSender:
    def __init__(self):
        self.passenger_bot = TeleBot(env.PASSENGER_BOT_TOKEN)
        self.driver_bot = TeleBot(env.DRIVER_BOT_TOKEN)
        self.max_retries = 2
        self.retry_delay = 1  # seconds

    def _get_bot(self, is_driver: bool):
        """Tegishli botni olish"""
        return self.driver_bot if is_driver else self.passenger_bot

    def _send_single_message(
            self,
            chat_id: int,
            message: str,
            parse_mode: str = "HTML",
            is_driver: bool = False,
            retry_count: int = 0
    ) -> bool:
        """Oddiy matn xabar yuborish - retry logic bilan"""
        try:
            bot = self._get_bot(is_driver)
            
            # parse_mode bo'sh bo'lsa ignore qilish
            if parse_mode:
                bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True,
                    timeout=15
                )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    disable_web_page_preview=True,
                    timeout=15
                )
            time.sleep(0.5)  # FloodWaitError bo'lmasligi uchun
            return True
        except Exception as e:
            error_str = str(e).lower()
            
            # Blok qilgan yoki fake user - retry qilmaymiz
            if any(keyword in error_str for keyword in ['blocked', 'bot was blocked', 'forbidden', 'user deleted']):
                print(f"User {chat_id} blocked bot - skipping")
                return False
            
            # Timeout yoki boshqa xato - retry qilamiz
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                return self._send_single_message(chat_id, message, parse_mode, is_driver, retry_count + 1)
            
            print(f"Message send failed for {chat_id} after {self.max_retries} retries: {e}")
            return False

    def _send_single_media(
            self,
            chat_id: int,
            media_type: str,
            media_file_bytes: bytes,
            filename: str,
            caption: str = "",
            parse_mode: str = "HTML",
            is_driver: bool = False,
            retry_count: int = 0
    ) -> bool:
        """Media xabar yuborish (rasm, video, audio, fayl) - retry logic bilan"""
        try:
            bot = self._get_bot(is_driver)
            file_stream = io.BytesIO(media_file_bytes)
            
            # Caption bo'sh bo'lsa ignore qilish
            caption_text = caption or ""
            
            if media_type == "photo":
                bot.send_photo(
                    chat_id=chat_id,
                    photo=file_stream,
                    caption=caption_text,
                    parse_mode=parse_mode if parse_mode else None,
                    timeout=30
                )
            elif media_type == "video":
                bot.send_video(
                    chat_id=chat_id,
                    video=file_stream,
                    caption=caption_text,
                    parse_mode=parse_mode if parse_mode else None,
                    timeout=30
                )
            elif media_type == "audio":
                bot.send_audio(
                    chat_id=chat_id,
                    audio=file_stream,
                    caption=caption_text,
                    parse_mode=parse_mode if parse_mode else None,
                    timeout=30
                )
            elif media_type == "document":
                bot.send_document(
                    chat_id=chat_id,
                    document=file_stream,
                    caption=caption_text,
                    parse_mode=parse_mode if parse_mode else None,
                    timeout=30
                )
            else:
                return False
            
            time.sleep(0.5)  # FloodWaitError bo'lmasligi uchun
            return True
        except Exception as e:
            error_str = str(e).lower()
            
            # Blok qilgan yoki fake user - retry qilmaymiz
            if any(keyword in error_str for keyword in ['blocked', 'bot was blocked', 'forbidden', 'user deleted']):
                print(f"User {chat_id} blocked bot - skipping media")
                return False
            
            # Timeout yoki boshqa xato - retry qilamiz
            if retry_count < self.max_retries:
                time.sleep(self.retry_delay)
                # BytesIO ni reset qilish
                file_stream = io.BytesIO(media_file_bytes)
                return self._send_single_media(
                    chat_id, media_type, media_file_bytes, filename,
                    caption, parse_mode, is_driver, retry_count + 1
                )
            
            print(f"Media send failed for {chat_id} after {self.max_retries} retries: {e}")
            return False

    def _send_batch_messages(self, batch_data, message, parse_mode="HTML", media_type="none", media_file_bytes=None,
                             media_filename=None):
        results = {'success': 0, 'failed': 0, 'failed_ids': [], 'blocked': 0}

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_id = {}
            for data in batch_data:
                telegram_id = data['id']
                is_driver = data.get('is_driver', False)

                if media_type != "none" and media_file_bytes:
                    future = executor.submit(
                        self._send_single_media,
                        telegram_id, media_type, media_file_bytes, media_filename,
                        message, parse_mode, is_driver
                    )
                else:
                    future = executor.submit(
                        self._send_single_message,
                        telegram_id, message, parse_mode, is_driver
                    )

                future_to_id[future] = telegram_id

            for future in concurrent.futures.as_completed(future_to_id, timeout=60):
                telegram_id = future_to_id[future]
                try:
                    ok = future.result(timeout=40)
                    if ok:
                        results['success'] += 1
                    else:
                        # Blocked user yoki xato
                        results['blocked'] += 1
                except concurrent.futures.TimeoutError:
                    # Timeout bo'lsa failed qilmaymiz, blocked hisoblaymiz
                    results['blocked'] += 1
                    print(f"Timeout for user {telegram_id}")
                except Exception as e:
                    results['failed'] += 1
                    results['failed_ids'].append(telegram_id)
                    print(f"Error for user {telegram_id}: {e}")

        return results

    def send_bulk(self, telegram_data, message, parse_mode="HTML", batch_size=100,
                  media_type="none", media_file_bytes=None, media_filename=None):
        results = {'success': 0, 'failed': 0, 'failed_ids': [], 'blocked': 0}

        for i in range(0, len(telegram_data), batch_size):
            batch = telegram_data[i:i + batch_size]
            batch_results = self._send_batch_messages(
                batch, message, parse_mode,
                media_type=media_type,
                media_file_bytes=media_file_bytes,
                media_filename=media_filename
            )
            results['success'] += batch_results['success']
            results['failed'] += batch_results['failed']
            results['blocked'] += batch_results.get('blocked', 0)
            results['failed_ids'].extend(batch_results['failed_ids'])
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

    def send_message_by_type(self, message_type, message, parse_mode="HTML", custom_ids=None,
                             media_type="none", media_file_bytes=None, media_filename=None):

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
            return self.send_bulk(
                telegram_data, message, parse_mode,
                media_type=media_type,
                media_file_bytes=media_file_bytes,
                media_filename=media_filename
            )
        return {'success': 0, 'failed': 0, 'failed_ids': []}