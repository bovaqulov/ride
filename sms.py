SMS_API = "AAFRLQAAvO8gsGS7XAIr5kQl2PFA8kMRIyn78Vu6x1yNgg"
from fastapi.middleware.cors import CORSMiddleware
import hmac
import hashlib
import json
import requests
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel


API_TOKEN = "AAFRLQAAvO8gsGS7XAIr5kQl2PFA8kMRIyn78Vu6x1yNgg"
GATEWAY_URL = "https://gatewayapi.telegram.org"
CALLBACK_URL = "https://e40891d0c579.ngrok-free.app/telegram-callback"


app = FastAPI()
origins = [
    "http://localhost:8080",
    "https://e40891d0c579.ngrok-free.app",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ------------------------
# Helper function: verify webhook
# ------------------------
def verify_webhook(req: Request, body: bytes) -> bool:
    ts = req.headers.get("X-Request-Timestamp")
    sig = req.headers.get("X-Request-Signature")
    if not ts or not sig:
        return False
    data_check = f"{ts}\n{body.decode('utf-8')}".encode("utf-8")
    secret_key = hashlib.sha256(API_TOKEN.encode()).digest()
    computed = hmac.new(secret_key, data_check, hashlib.sha256).hexdigest()
    return hmac.compare_digest(computed, sig)

# ------------------------
# Request models
# ------------------------
class PhoneRequest(BaseModel):
    phone_number: str  # E.164 format: +998901234567

class CodeRequest(BaseModel):
    request_id: str
    code: str

# ------------------------
# Step 1: Check send ability
# ------------------------
@app.post("/check-send-ability")
def check_send_ability(data: PhoneRequest):
    payload = {"phone_number": data.phone_number}
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(f"{GATEWAY_URL}/checkSendAbility", json=payload, headers=headers)
    result = response.json()
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    # Return request_id to use for sending code
    return result["result"]

# ------------------------
# Step 2: Send verification code
# ------------------------
@app.post("/send-code")
def send_code(data: PhoneRequest, code_length: int = 6):
    payload = {
        "phone_number": data.phone_number,
        "code_length": code_length,
        "callback_url": CALLBACK_URL,
    }
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(f"{GATEWAY_URL}/sendVerificationMessage", json=payload, headers=headers)
    result = response.json()
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result["result"]

# ------------------------
# Step 3: Verify code entered by user
# ------------------------
@app.post("/verify-code")
def verify_code(data: CodeRequest):
    payload = {"request_id": data.request_id, "code": data.code}
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.post(f"{GATEWAY_URL}/checkVerificationStatus", json=payload, headers=headers)
    result = response.json()
    if not result.get("ok"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result["result"]

# ------------------------
# Step 4: Webhook to receive delivery reports
# ------------------------
@app.post("/telegram-callback")
async def telegram_callback(request: Request):
    body = await request.body()
    if not verify_webhook(request, body):
        raise HTTPException(status_code=403, detail="Invalid signature")
    payload = await request.json()
    # Bu yerda payload RequestStatus obyekt bo'ladi
    # Masalan: payload["delivery_status"]["status"], payload["request_id"]
    print("Webhook payload:", json.dumps(payload, indent=2))
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
