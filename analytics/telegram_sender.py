import asyncio
from typing import Iterable, List, Dict, Union, Optional

import aiohttp
from asgiref.sync import async_to_sync
from django.db.models import QuerySet

from bot_app.models import BotClient, Driver
from configuration import env


TelegramId = Union[int, str]


class TelegramSender:
    def __init__(self, concurrency: int = 25, timeout_sec: int = 15):
        self.passenger_bot_token = env.PASSENGER_BOT_TOKEN
        self.driver_bot_token = env.DRIVER_BOT_TOKEN

        # to'g'ri template: token ham shu yerda kiradi
        self.base_url_tmpl = "https://api.telegram.org/bot{token}/{method}"

        self.concurrency = concurrency
        self.timeout = aiohttp.ClientTimeout(total=timeout_sec)

    # -------------------------
    # Token routing helpers
    # -------------------------
    def _normalize_ids(self, ids: Iterable[TelegramId]) -> List[int]:
        out: List[int] = []
        for x in ids:
            if x is None:
                continue
            try:
                out.append(int(str(x).strip()))
            except Exception:
                # yaroqsiz idlar tashlab ketiladi
                continue
        return out

    def _get_driver_id_set(self, telegram_ids: List[int]) -> set[int]:
        """
        Bulk routing uchun: berilgan IDlar orasidan qaysilari Driver ekanini bitta query bilan olamiz.
        """
        if not telegram_ids:
            return set()
        return set(
            Driver.objects.filter(telegram_id__in=telegram_ids)
            .values_list("telegram_id", flat=True)
        )

    def _token_for_id(self, telegram_id: int, driver_id_set: Optional[set[int]] = None) -> str:
        if driver_id_set is not None:
            return self.driver_bot_token if telegram_id in driver_id_set else self.passenger_bot_token

        # single send uchun (bitta query) – tez-tez chaqirilsa bulk ishlating
        is_driver = Driver.objects.filter(telegram_id=telegram_id).exists()
        return self.driver_bot_token if is_driver else self.passenger_bot_token

    # -------------------------
    # HTTP send
    # -------------------------
    async def _send_message(
        self,
        session: aiohttp.ClientSession,
        token: str,
        chat_id: int,
        message: str,
        parse_mode: str = "HTML",
    ) -> bool:
        url = self.base_url_tmpl.format(token=token, method="sendMessage")
        payload = {"chat_id": chat_id, "text": message, "parse_mode": parse_mode}

        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json(content_type=None)
                return bool(data.get("ok", False))
        except Exception:
            return False

    async def send_bulk_async(
        self,
        telegram_ids: Iterable[TelegramId],
        message: str,
        parse_mode: str = "HTML",
    ) -> Dict:
        ids = self._normalize_ids(telegram_ids)
        results = {"success": 0, "failed": 0, "failed_ids": []}

        if not ids:
            return results

        driver_id_set = self._get_driver_id_set(ids)
        sem = asyncio.Semaphore(self.concurrency)

        async with aiohttp.ClientSession(timeout=self.timeout) as session:

            async def _one(chat_id: int):
                async with sem:
                    token = self._token_for_id(chat_id, driver_id_set=driver_id_set)
                    ok = await self._send_message(session, token, chat_id, message, parse_mode=parse_mode)
                    return chat_id, ok

            tasks = [asyncio.create_task(_one(chat_id)) for chat_id in ids]

            for coro in asyncio.as_completed(tasks):
                chat_id, ok = await coro
                if ok:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["failed_ids"].append(chat_id)

        return results

    def send_bulk(self, telegram_ids: Iterable[TelegramId], message: str, parse_mode: str = "HTML") -> Dict:
        """
        Django admin view (sync) uchun eng toza yo'l: async_to_sync.
        """
        return async_to_sync(self.send_bulk_async)(telegram_ids, message, parse_mode)

    def send_to_user(self, telegram_id: TelegramId, message: str, parse_mode: str = "HTML") -> bool:
        r = self.send_bulk([telegram_id], message, parse_mode=parse_mode)
        return r.get("success", 0) == 1

    # -------------------------
    # High-level targets
    # -------------------------
    def send_to_all_users(self, message: str, exclude_banned: bool = True) -> Dict:
        qs: QuerySet[BotClient] = BotClient.objects.all()
        if exclude_banned:
            qs = qs.filter(is_banned=False)

        ids = list(qs.values_list("telegram_id", flat=True))
        return self.send_bulk(ids, message)

    def send_to_all_drivers(self, message: str) -> Dict:
        ids = list(
            Driver.objects.exclude(telegram_id__isnull=True)
            .values_list("telegram_id", flat=True)
        )
        return self.send_bulk(ids, message)

    def send_to_everyone(self, message: str, exclude_banned_users: bool = True) -> Dict:
        """
        'all' rejimi: passenger + driver hammasiga yuboradi.
        Driver bo'lsa driver token bilan ketadi, qolganlar passenger token bilan.
        """
        user_qs: QuerySet[BotClient] = BotClient.objects.all()
        if exclude_banned_users:
            user_qs = user_qs.filter(is_banned=False)

        user_ids = list(user_qs.values_list("telegram_id", flat=True))
        driver_ids = list(
            Driver.objects.exclude(telegram_id__isnull=True)
            .values_list("telegram_id", flat=True)
        )

        # dublikatlarni yo'qotamiz
        all_ids = list({*self._normalize_ids(user_ids), *self._normalize_ids(driver_ids)})
        return self.send_bulk(all_ids, message)
