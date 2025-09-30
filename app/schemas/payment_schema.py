import strawberry
from typing import Optional, List


# -----------------------------
# 📌 Tipos (outputs)
# -----------------------------
@strawberry.type
class ItemType:
    title: str
    quantity: int
    unit_price: float = strawberry.field(name="unitPrice")
    currency_id: Optional[str] = strawberry.field(name="currencyId")


@strawberry.type
class PayerType:
    email: Optional[str] = None
    name: Optional[str] = None


@strawberry.type
class Payment:
    id: str
    init_point: Optional[str] = strawberry.field(name="initPoint")
    sandbox_init_point: Optional[str] = strawberry.field(name="sandboxInitPoint")
    external_reference: Optional[str] = strawberry.field(name="externalReference")
    items: Optional[List[ItemType]]
    payer: Optional[PayerType]
    date_created: Optional[str] = strawberry.field(name="dateCreated")


# -----------------------------
# 📌 Inputs
# -----------------------------
@strawberry.input
class ItemInput:
    title: str
    quantity: int
    unit_price: float = strawberry.field(name="unitPrice")
    currency_id: Optional[str] = strawberry.field(name="currencyId", default="ARS")


@strawberry.input
class PreferenceInput:
    items: List[ItemInput]
    external_reference: Optional[str] = strawberry.field(name="externalReference", default=None)
