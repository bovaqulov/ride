# Telegram Sender - pytelegrambotapi bilan

Faylni qayta yozdim **pyTelegramBotAPI** kutubxonasi orqali ishlaydi.

## O'zgarishlar:

### 1. **Imports**
```python
from telebot import TeleBot  # requests o'rniga
```

### 2. **Bot Initialization**
```python
self.passenger_bot = TeleBot(env.PASSENGER_BOT_TOKEN)
self.driver_bot = TeleBot(env.DRIVER_BOT_TOKEN)
```

### 3. **Methods**
- `_send_single_message()` - Matn xabar yuborish
- `_send_single_media()` - Media (rasm, video, audio, fayl) yuborish
- `_get_bot()` - Tegishli bot instanceni olish
- Boshqa methodlar o'zgarishsiz

### 4. **Media Support**
- 📸 **Photo** - `send_photo()`
- 🎥 **Video** - `send_video()`
- 🎵 **Audio** - `send_audio()`
- 📄 **Document** - `send_document()`

## Afzalliklari:

✅ API endpoint orqali requests yuborish kerak emas
✅ Async/sync dual support (Optional)
✅ Aniqroq error handling
✅ Type hints bilan ishlaydi
✅ Birorta xotira yo'q

## Admin Panel ishlashi:

```
Admin Panel → Xabar jo'natish → TelegramSender → pyTelegramBotAPI → Telegram Bot
```

## Setup:
```bash
pip install pyTelegramBotAPI  # allaqachon o'rnatilgan
python manage.py runserver
```

Barcha xabar tiplari to'liq ishlaydi! 🎉
