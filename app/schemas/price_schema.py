import strawberry

@strawberry.type
class Price:
    credits: int
    cost: float
    currency: str


@strawberry.type
class PriceQuery:
    @strawberry.field
    def price(self, credits: int) -> Price:
        PRICE_TABLE = {
            250: 5.0,    # 250 créditos → 5 USD
            750: 12.0,   # 750 créditos → 12 USD
            1500: 20.0,  # 1500 créditos → 20 USD
        }

        cost = PRICE_TABLE.get(credits)
        if not cost:
            raise ValueError("Cantidad de créditos no válida")

        return Price(credits=credits, cost=cost, currency="USD")
