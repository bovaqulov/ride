import hashlib
import requests

# =====================
# 1️⃣ SIPUNI ma'lumotlari
# =====================
user = '095511'  # SIPUNI akkaunt raqami
secret = '0.wnze0f2qrfk'

# =====================
# 2️⃣ Qo'ng'iroq ma'lumotlari
# =====================
phone_from_client = '998330667378'  # Mijoz 1
office_sipnumber = '204'      # Ofis telefoni
phone_to_client = '998912798223'   # Mijoz 2

# =====================
# 3️⃣ Oldindan yaratilgan call_tree sxema ID si
# =====================
# SIPUNI panelida yaratgan sxemangiz: Mijoz1 → Ofis → Mijoz2
tree_id = '3824685'

reverse = '0'             # 0 - qo'ng'iroq birinchi mijozga boradi
call_attempt_time = 35    # maksimal urinish vaqti (sekund)

# =====================
# 4️⃣ Hash hosil qilish
# =====================
hash_string = '+'.join([
    str(call_attempt_time),
    phone_from_client,
    reverse,
    office_sipnumber,
    tree_id,
    user,
    secret
])
hash_md5 = hashlib.md5(hash_string.encode()).hexdigest()

# =====================
# 5️⃣ API so'rov yuborish
# =====================
url = 'https://sipuni.com/api/callback/call_tree'
data = {
    'callAttemptTime': call_attempt_time,
    'phone': phone_from_client,
    'reverse': reverse,
    'sipnumber': office_sipnumber,
    'tree': tree_id,
    'user': user,
    'hash': hash_md5
}

response = requests.post(url, data=data)
result = response.json()

print("API javobi:", result)

# =====================
# 6️⃣ CallbackId ni olish va keyin kerak bo'lsa bekor qilish
# # =====================
# callback_id = result.get('callbackId')

# if callback_id:
#     print("CallbackId:", callback_id)
#
#     # Misol uchun: qo'ng'iroqni bekor qilish
#     hash_cancel = hashlib.md5(f"{callback_id}+{user}+{secret}".encode()).hexdigest()
#     cancel_url = 'https://sipuni.com/api/callback/cancel'
#     cancel_response = requests.post(cancel_url, data={
#         'callbackId': callback_id,
#         'user': user,
#         'hash': hash_cancel
#     })
#     print("Bekor qilish javobi:", cancel_response.json())
