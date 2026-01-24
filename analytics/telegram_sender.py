import asyncio
import aiohttp
from typing import List

from bot_app.models import BotClient, Driver
from configuration import env


class TelegramSender:
    def __init__(self):
        self.passenger_bot_token = env.PASSENGER_BOT_TOKEN
        self.driver_bot_token = env.DRIVER_BOT_TOKEN

        self.base_url = "https://api.telegram.org/bot{}"

    def _get_bot_token(self, is_driver: bool = False) -> str:
        """Foydalanuvchi turiga qarab bot tokenni qaytarish"""
        return self.driver_bot_token if is_driver else self.passenger_bot_token

    def _get_base_url(self, is_driver: bool = False) -> str:
        """Foydalanuvchi turiga qarab base URL yaratish"""
        token = self._get_bot_token(is_driver)
        return f"https://api.telegram.org/bot{token}"

    async def _send_message_async(self, chat_id: int, message: str,
                                  parse_mode: str = "HTML", is_driver: bool = False) -> bool:
        """Async tarzda xabar yuborish"""
        async with aiohttp.ClientSession() as session:
            url = f"{self._get_base_url(is_driver)}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            try:
                async with session.post(url, json=payload, timeout=10) as response:
                    result = await response.json()
                    return result.get('ok', False)
            except asyncio.TimeoutError:
                print(f"Timeout xatosi: {chat_id} ga xabar yuborishda")
                return False
            except Exception as e:
                print(f"Xatolik yuz berdi: {e}")
                return False

    def send_to_user(self, telegram_id: int, message: str, is_driver: bool = False) -> None:
        """Bitta foydalanuvchiga xabar yuborish"""
        try:
            # Sync versiya - event loop bilan ishlash
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self._send_message_async(telegram_id, message, is_driver=is_driver)
            )
            return result
        except Exception as e:
            print(f"Xatolik: {e}")
            return False
        finally:
            if loop.is_running():
                loop.close()

    async def send_bulk_async(self, telegram_data: List[dict], message: str) -> dict:
        """Bir nechta foydalanuvchilarga async tarzda xabar yuborish

        Args:
            telegram_data: Har bir element {'id': int, 'is_driver': bool} formatida
            message: Yuboriladigan xabar
        """
        results = {
            'success': 0,
            'failed': 0,
            'failed_ids': []
        }

        # Barcha xabarlarni parallel yuborish
        tasks = []
        for data in telegram_data:
            telegram_id = data['id']
            is_driver = data.get('is_driver', False)
            task = self._send_message_async(telegram_id, message, is_driver=is_driver)
            tasks.append((telegram_id, task))

        # Natijalarni kuzatish
        for telegram_id, task in tasks:
            try:
                success = await task
                if success:
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['failed_ids'].append(telegram_id)
            except Exception as e:
                results['failed'] += 1
                results['failed_ids'].append(telegram_id)
                print(f"Xatolik {telegram_id}: {e}")

        return results

    def send_bulk(self, telegram_data: List[dict], message: str) -> dict:
        """Bulk xabar yuborish (sync wrapper)"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            results = loop.run_until_complete(
                self.send_bulk_async(telegram_data, message)
            )
            return results
        except Exception as e:
            print(f"Bulk xabar yuborishda xatolik: {e}")
            return {'success': 0, 'failed': len(telegram_data), 'failed_ids': [d['id'] for d in telegram_data]}
        finally:
            if loop.is_running():
                loop.close()

    def get_all_users_data(self, exclude_banned: bool = True) -> List[dict]:
        """Barcha foydalanuvchilar uchun telegram ma'lumotlarini olish"""
        queryset = BotClient.objects.all()
        if exclude_banned:
            queryset = queryset.filter(is_banned=False)

        users_data = []
        for user in queryset:
            # Agar user driver bo'lsa, driver bot orqali yuboramiz
            is_driver = hasattr(user, 'driver') and user.driver is not None
            users_data.append({
                'id': user.telegram_id,
                'is_driver': is_driver
            })

        return users_data

    def get_all_drivers_data(self) -> List[dict]:
        """Barcha haydovchilar uchun telegram ma'lumotlarini olish"""
        drivers = Driver.objects.filter(telegram_id__isnull=False)
        return [{'id': d.telegram_id, 'is_driver': True} for d in drivers]

    def send_to_all_users(self, message: str, exclude_banned: bool = True) -> dict:
        """Barcha foydalanuvchilarga xabar yuborish (haydovchi bo'lsa driver bot orqali)"""
        users_data = self.get_all_users_data(exclude_banned)
        return self.send_bulk(users_data, message)

    def send_to_all_drivers(self, message: str) -> dict:
        """Barcha haydovchilarga xabar yuborish (driver bot orqali)"""
        drivers_data = self.get_all_drivers_data()
        return self.send_bulk(drivers_data, message)

    def send_to_all_passengers(self, message: str) -> dict:
        """Barcha yo'lovchilarga xabar yuborish (passenger bot orqali)"""
        from bot_app.models import Passenger
        passengers = Passenger.objects.filter(telegram_id__isnull=False)
        passengers_data = [{'id': p.telegram_id, 'is_driver': False} for p in passengers]
        return self.send_bulk(passengers_data, message)

    def send_to_both_groups(self, message: str) -> dict:
        """Ham haydovchilar, ham yo'lovchilarga xabar yuborish"""
        # Haydovchilar
        drivers_data = self.get_all_drivers_data()

        # Yo'lovchilar
        from bot_app.models import Passenger
        passengers = Passenger.objects.filter(telegram_id__isnull=False)
        passengers_data = [{'id': p.telegram_id, 'is_driver': False} for p in passengers]

        # Barchasini birlashtirish
        all_data = drivers_data + passengers_data

        # Duplikatlarni olib tashlash
        unique_data = []
        seen_ids = set()
        for data in all_data:
            if data['id'] not in seen_ids:
                seen_ids.add(data['id'])
                unique_data.append(data)

        return self.send_bulk(unique_data, message)

    def send_to_custom_users(self, telegram_ids: List[int], message: str) -> dict:
        """Maxsus telegram ID lariga xabar yuborish (avtomatik ravishda driver/passenger aniqlash)"""
        users_data = []

        for telegram_id in telegram_ids:
            # User driver ekanligini tekshirish
            is_driver = False
            try:
                # BotClient orqali tekshirish
                user = BotClient.objects.filter(telegram_id=telegram_id).first()
                if user and hasattr(user, 'driver') and user.driver is not None:
                    is_driver = True
                else:
                    # To'g'ridan-to'g'ri Driver modelida tekshirish
                    driver = Driver.objects.filter(telegram_id=telegram_id).first()
                    if driver:
                        is_driver = True
            except Exception:
                pass

            users_data.append({
                'id': telegram_id,
                'is_driver': is_driver
            })

        return self.send_bulk(users_data, message)