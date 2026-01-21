import asyncio
import aiohttp
from typing import List

from bot_app.models import BotClient
from bot_app.models import Driver
from configuration import env


class TelegramSender:
    def __init__(self):
        self.bot_token = env.MAIN_BOT
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"

    async def _send_message_async(self, chat_id: int, message: str, parse_mode: str = "HTML"):
        """Async tarzda xabar yuborish"""
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': parse_mode
            }

            try:
                async with session.post(url, json=payload) as response:
                    result = await response.json()
                    return result.get('ok', False)
            except Exception as e:
                print(f"Xatolik yuz berdi: {e}")
                return False

    def send_to_user(self, telegram_id: int, message: str) -> bool:
        """Bitta foydalanuvchiga xabar yuborish"""
        try:
            # Sync versiya - event loop bilan ishlash
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self._send_message_async(telegram_id, message)
            )
            loop.close()
            return result
        except Exception as e:
            print(f"Xatolik: {e}")
            return False

    async def send_bulk_async(self, telegram_ids: List[int], message: str) -> dict:
        """Bir nechta foydalanuvchilarga async tarzda xabar yuborish"""
        results = {
            'success': 0,
            'failed': 0,
            'failed_ids': []
        }

        tasks = []
        for telegram_id in telegram_ids:
            task = self._send_message_async(telegram_id, message)
            tasks.append((telegram_id, task))

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

    def send_bulk(self, telegram_ids: List[int|str], message: str) -> dict:
        """Bulk xabar yuborish (sync wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(
                self.send_bulk_async(telegram_ids, message)
            )
            loop.close()
            return results
        except Exception as e:
            print(f"Bulk xabar yuborishda xatolik: {e}")
            return {'success': 0, 'failed': len(telegram_ids), 'failed_ids': telegram_ids}

    def send_to_all_users(self, message: str, exclude_banned: bool = True) -> dict:
        """Barcha foydalanuvchilarga xabar yuborish"""
        queryset = BotClient.objects.all()
        if exclude_banned:
            queryset = queryset.filter(is_banned=False)

        telegram_ids = list(queryset.values_list('telegram_id', flat=True))
        return self.send_bulk(telegram_ids, message)

    def send_to_all_drivers(self, message: str) -> dict:


        drivers = Driver.objects.all()
        telegram_ids = [d.telegram_id for d in drivers if d.telegram_id]
        return self.send_bulk(telegram_ids, message)

