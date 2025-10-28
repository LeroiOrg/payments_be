import strawberry
from app.services.payment_service import MercadoPagoService
from app.schemas.payment_schema import Payment, PreferenceInput, ItemType, PayerType
from dotenv import load_dotenv
import os

load_dotenv()

PAYMENT_BE_URL = os.getenv("PAYMENT_BE_URL")
LEROI_FRONT = os.getenv("LEROI_FRONT")
mp_service = MercadoPagoService()


@strawberry.type
class PaymentMutation:
    @strawberry.mutation
    def create_preference(self, input: PreferenceInput) -> Payment:
        # Construir payload para MercadoPago
        pref_data = {
            "items": [item.__dict__ for item in input.items],
            "external_reference": input.external_reference,
            "auto_return": "approved",
            "back_urls": {
                "success": f"{LEROI_FRONT}/paymentSuccess",
                "failure": f"{LEROI_FRONT}/paymentFailure",
                "pending": f"{LEROI_FRONT}",
            },
            "notification_url": f"{PAYMENT_BE_URL}/webhooks/mercadopago",  # webhook
        }


        # Llamar al servicio de MercadoPago
        resp = mp_service.create_preference(pref_data)
        pref = resp["response"]

        # 🔎 Debug: imprimir respuesta completa de MP
        print("Respuesta MP:", pref)

        # Mapear respuesta a tipo GraphQL
        return Payment(
            id=pref.get("id") or pref.get("preference_id"),
            init_point=pref.get("init_point"),
            sandbox_init_point=pref.get("sandbox_init_point"),
            external_reference=pref.get("external_reference"),
            items=[
                ItemType(
                    title=i["title"],
                    quantity=i["quantity"],
                    unit_price=i["unit_price"],
                    currency_id=i.get("currency_id")
                )
                for i in pref.get("items", [])
            ],
            payer=PayerType(
                email=pref.get("payer", {}).get("email"),
                name=pref.get("payer", {}).get("name")
            ) if pref.get("payer") else None,
            date_created=pref.get("date_created"),
        )