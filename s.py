import hashlib
import requests

user = "095511"  # Sizning account raqamingiz
secret = "0.wnze0f2qrfk"  # Integration secret key

def make_call(phone_from, phone_to, sipnumber, sipnumber2):
    url = "https://sipuni.com/api/callback/call_external"


    # Hash string yaratamiz
    hash_string = f"{phone_from}+{phone_to}+{sipnumber}+{sipnumber2}+{user}+{secret}"
    hash_md5 = hashlib.md5(hash_string.encode()).hexdigest()

    payload = {
        "phoneFrom": phone_from,
        "phoneTo": phone_to,
        "sipnumber": sipnumber,
        "sipnumber2": sipnumber2,
        "user": user,
        "hash": hash_md5
    }

    response = requests.post(url, data=payload)
    return response.json()

CALLBACK_CANCEL_URL = "https://sipuni.com/api/callback/cancel"

def cancel_call(call_id: str):
    # hash yaratish: callbackId + user + secret
    hash_string = f"{call_id}+{user}+{secret}"
    hash_md5 = hashlib.md5(hash_string.encode('utf-8')).hexdigest()

    payload = {
        "callbackId": call_id,
        "user": user,
        "hash": hash_md5
    }

    r = requests.post(CALLBACK_CANCEL_URL, data=payload)
    return r.json()




# TEST CALL (Misol sifatida)
if __name__ == "__main__":
    # result = make_call(
    #     phone_from="998912798223",   # passenger real number
    #     phone_to="998330667378",     # driver real number
    #     sipnumber="204",          # SIP internal number 1
    #     sipnumber2="204"          # SIP internal number 2 (shu bilan ham bo'ladi)
    # )
    result = cancel_call("68c50bab633c2f2aa761b9b49283a55")
    print("Natija:", result)
