import strawberry
import uuid
from strawberry.types import Info
from app.models.credit_transaction import CreditTransaction

@strawberry.type
class SessionType:
    session_id: str

@strawberry.type
class SessionMutation:
    @strawberry.mutation
    def create_session(
        self,
        info: Info,
        authToken: str,
        credits: int,
        email: str,
    ) -> SessionType:
        db = info.context["db"]

        session_id = str(uuid.uuid4())

        transaction = CreditTransaction(
            email=email,
            credits=credits,
            token=authToken,
            session_id=session_id,
            payment_id="",
            status="pending"
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return SessionType(session_id=session_id)
