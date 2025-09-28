from fastapi import APIRouter, Request
import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()  # carga .env en os.environ

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
ACCESS_TOKEN_PROVISIONAL = os.getenv("ACCESS_TOKEN_PROVISIONAL")

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
                headers = {"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            )
            resp.raise_for_status()  # <-- Esto lanza excepción si no es 2xx
            payment_info = resp.json()
            print("Pago consultado:", payment_info)

            if payment_info.get("status") == "approved":
                ref_data = json.loads(payment_info.get("external_reference"))
                email = ref_data["email"]
                credits_to_add = ref_data["credits"]
                credits_to_add_str = str(credits_to_add)
                print("Creditos añadidos correctamente " + credits_to_add_str)
                user_token = ACCESS_TOKEN_PROVISIONAL

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
