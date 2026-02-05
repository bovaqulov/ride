# analytics/tasks.py
from celery import shared_task
import logging
from .telegram_sender import TelegramSender

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_bulk_message(self, telegram_data, message, parse_mode="HTML", batch_size=100,
                      media_type="none", media_file_bytes=None, media_filename=None):
    """
    Bulk xabarllarni asynchronously yuborish
    Celery task sifatida RAM yeyishni kamaytirish uchun
    """
    try:
        sender = TelegramSender()
        results = sender.send_bulk(
            telegram_data=telegram_data,
            message=message,
            parse_mode=parse_mode,
            batch_size=batch_size,
            media_type=media_type,
            media_file_bytes=media_file_bytes,
            media_filename=media_filename
        )
        logger.info(f"Bulk message sent: {results}")
        return results
    except Exception as e:
        logger.error(f"Error in send_bulk_message: {e}")
        raise self.retry(exc=e, countdown=60)  # 1 daqiqada retry


@shared_task
def send_single_message(telegram_id: int, message: str, parse_mode: str = "HTML", is_driver: bool = False):
    """
    Bitta xabar yuborish
    """
    try:
        sender = TelegramSender()
        result = sender._send_single_message(telegram_id, message, parse_mode, is_driver)
        return result
    except Exception as e:
        logger.error(f"Error sending message to {telegram_id}: {e}")
        raise
