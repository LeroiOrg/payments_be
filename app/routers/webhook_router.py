from fastapi import APIRouter, Request, Depends
import requests, json, os
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from app.db.session import SessionLocal
from app.models.credit_transaction import CreditTransaction
from app.pubsub.pubsub_client import publish_event

load_dotenv()
router = APIRouter()

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

# Dependencia DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/webhooks/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]

            # Consultar pago
            resp = requests.get(
                f"https://api.mercadopago.com/v1/payments/{payment_id}",
                headers={"Authorization": f"Bearer {MP_ACCESS_TOKEN}"}
            )
            resp.raise_for_status()
            payment_info = resp.json()

            status = payment_info.get("status")
            external_reference = payment_info.get("external_reference")
            ref_data = json.loads(external_reference)
            session_id = ref_data.get("sessionId")

            print(f"La sesión es: {session_id} | Status del pago: {status}")

            # Buscar en la DB la sesión con session_id
            transaction = db.query(CreditTransaction).filter_by(
                session_id=session_id
            ).first()

            if not transaction:
                raise Exception("Sesión no encontrada en DB")

            # Actualizar transacción según el estado del pago
            transaction.payment_id = str(payment_id)
            if status == "approved":
                transaction.status = "approved"
                db.commit()
                print(f"Créditos aprobados para {transaction.email}")

                event_payload = {
                    "email": transaction.email,
                    "credits": transaction.credits,
                    "session_id": transaction.session_id,
                    "status": status,
                    "payment_id": str(payment_id)
                }
                publish_event("payment_status_changed", event_payload)

                print(f"Evento publicado en Pub/Sub: {event_payload}")
                print("Update credits response:")

            elif status in ["rejected", "cancelled"]:
                transaction.status = "failed"
                db.commit()
                print(f"Pago fallido para {transaction.email}")
                publish_event("payment_status_changed", "Pago fallido")

            elif status == "pending":
                transaction.status = "pending"
                db.commit()
                print(f"Pago pendiente para {transaction.email}")
                publish_event("payment_status_changed", "Pago pendiente")

            else:
                transaction.status = status
                db.commit()
                print(f"Pago con estado {status} para {transaction.email}")

        return {"status": "ok"}

    except Exception as e:
        print("ERROR en webhook:", e)
        return {"status": "error", "detail": str(e)}
