from app.db.session import Base, engine

if __name__ == "__main__":
    print("⚠️ Esto va a borrar TODAS las tablas y recrearlas")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tablas recreadas correctamente")
