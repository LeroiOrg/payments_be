import os
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter
from app.schemas.schema import schema
from app.routers import webhook_router
from app.db.session import Base, engine
from app.db.session import SessionLocal
from dotenv import load_dotenv

load_dotenv()
LEROI_FRONT = os.getenv("LEROI_FRONT")

def get_context():
    db = SessionLocal()
    return {"db": db}

# Crear tablas en la DB
try:
    Base.metadata.create_all(bind=engine)
    print("Conexión a la base de datos establecida correctamente.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}")

app = FastAPI(title="Payments Services prueba", version="2.0")

ALLOWED_ORIGINS = [LEROI_FRONT, "http://localhost:5173","http://localhost:3000","http://localhost:3001","https://leroi-front-next.vercel.app"]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta de prueba
@app.get("/ping")
async def ping():
    return {"status": "ok", "message": "Servidor funcionando"}

# GraphQL
graphql_app = GraphQLRouter(schema, context_getter=get_context)
app.include_router(graphql_app, prefix="/payments-be", tags=["payments-be"])

# REST: webhook
app.include_router(webhook_router.router)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)