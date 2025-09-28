import strawberry
from app.schemas.price_schema import PriceQuery
from app.mutations.payment_mutation import PaymentMutation
from app.schemas.transaction_schema import TransactionMutation


# -----------------------------
# 📌 Query principal
# -----------------------------
@strawberry.type
class Query(PriceQuery):   # hereda de PriceQuery
    @strawberry.field
    def ping(self) -> str:
        return "pong"


# -----------------------------
# 📌 Mutations raíz
# -----------------------------
@strawberry.type
class Mutation(PaymentMutation, TransactionMutation):
    pass


# -----------------------------
# 📌 Schema principal
# -----------------------------
schema = strawberry.Schema(query=Query, mutation=Mutation)