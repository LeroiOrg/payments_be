from fastapi import APIRouter, Request
import requests
import json

router = APIRouter()
UPDATE_CREDITS_URL = "http://3.16.158.35:8000/user-credits"

@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request):
    try:
        data = await request.json()
        print("Webhook recibido:", data)

        if data.get("type") == "payment":
            payment_id = data["data"]["id"]

            # Consultar pago en MercadoPago
            resp = requests.get(
                f"https://api.mercadopago.com/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer APP_USR-4772830502714206-092222-5b4d945840e0a3383252dbaebe85d300-2703406219"}
            )
            resp.raise_for_status()  # <-- Esto lanza excepción si no es 2xx
            payment_info = resp.json()
            print("Pago consultado:", payment_info)

            if payment_info.get("status") == "approved":
                #ref_data = json.loads(external_reference)
                email = "kristian.b2403@gmail.com"
                credits_to_add = 250
                user_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo2LCJmaXJzdF9uYW1lIjoiQ3Jpc3RpYW4iLCJsYXN0X25hbWUiOiIiLCJlbWFpbCI6ImtyaXN0aWFuLmIyNDAzQGdtYWlsLmNvbSIsInByb3ZpZGVyIjoiZW1haWwiLCJ0ZmFfZW5hYmxlZCI6ZmFsc2UsImV4cCI6MTc1OTAyOTE5MH0.LZTCVbGvdpi6ZiAmHvd-bRY7z6esR100tDI20maVUPQ"

                # Llamar al endpoint PATCH
                update_resp = requests.patch(
                    f"{UPDATE_CREDITS_URL}/{email}",
                    headers={
                        "Authorization": f"Bearer {user_token}",
                        "Content-Type": "application/json"
                    },
                    json={"amount": credits_to_add}
                )
                update_resp.raise_for_status()
                print("Update credits response:", update_resp.json())

        return {"status": "ok"}

    except Exception as e:
        print("ERROR en webhook:", e)
        return {"status": "error", "detail": str(e)}
