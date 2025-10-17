import strawberry
from typing import Optional
from app.services.payment_service import MercadoPagoService

mp_service = MercadoPagoService()


# -----------------------------
# Tipos
# -----------------------------
@strawberry.type
class Transaction:
    id: str
    status: str
    transaction_amount: float
    payer_email: Optional[str]


# -----------------------------
# Mutations
# -----------------------------
@strawberry.type
class TransactionMutation:
    @strawberry.mutation
    def get_transaction(self, payment_id: str) -> Transaction:
        resp = mp_service.sdk.payment().get(payment_id)
        data = resp["response"]

        return Transaction(
            id=data["id"],
            status=data["status"],
            transaction_amount=data["transaction_amount"],
            payer_email=data.get("payer", {}).get("email"),
        )
