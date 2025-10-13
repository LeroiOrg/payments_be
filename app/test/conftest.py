"""
Configuración segura de pytest para payments_be
- Base de datos en memoria (SQLite)
- Mocks de APIs externas
- Fixtures reutilizables
"""

import pytest
import os

# ✅ CONFIGURAR ENTORNO ANTES DE IMPORTAR CUALQUIER COSA
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["MP_ACCESS_TOKEN"] = "TEST_MP_TOKEN"
os.environ["AUTH_SERVICE_URL"] = "http://localhost:8001"

from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from faker import Faker

# Importaciones del proyecto - ahora con env vars configuradas
from app.db.session import Base
from app.models.credit_transaction import CreditTransaction
from app.main import app

# Configurar Faker para datos de prueba
fake = Faker()

# ===== CONFIGURACIÓN DE BASE DE DATOS DE PRUEBAS =====

@pytest.fixture(scope="function")
def test_engine():
    """Engine de SQLite en memoria para pruebas - se destruye al final"""
    # ✅ Base de datos completamente separada - SQLite en memoria
    from sqlalchemy.pool import StaticPool
    
    engine = create_engine(
        "sqlite:///:memory:", 
        poolclass=StaticPool,
        connect_args={
            "check_same_thread": False,
        },
        echo=False  # Sin logs SQL en pruebas
    )
    
    # ✅ Crear todas las tablas en memoria
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # ✅ Limpiar al finalizar
    engine.dispose()


@pytest.fixture(scope="function") 
def test_db(test_engine):
    """Sesión de base de datos de pruebas - limpia automáticamente"""
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSessionLocal()
    
    try:
        yield db
    finally:
        # ✅ Rollback automático - no queda rastro
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def test_client(test_db):
    """Cliente de FastAPI para pruebas HTTP"""
    from app.routers.webhook_router import get_db
    
    def override_get_db():
        try:
            yield test_db
        finally:
            pass  # La sesión se maneja en test_db fixture
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Limpiar override
    app.dependency_overrides.clear()


# ===== FIXTURES DE DATOS DE PRUEBA =====

@pytest.fixture
def sample_credit_transaction_data():
    """Datos válidos para crear CreditTransaction"""
    return {
        "email": fake.email(),
        "credits": fake.random_int(min=50, max=1000),
        "status": "pending",
        "payment_id": f"MP_{fake.random_int(min=10000, max=99999)}",
        "session_id": fake.uuid4(),
        "token": f"jwt.{fake.pystr()}.{fake.pystr()}"
    }


@pytest.fixture
def valid_jwt_token():
    """Token JWT válido simulado"""
    return "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InRlc3RAdGVzdC5jb20ifQ.test"


@pytest.fixture
def webhook_payload():
    """Payload típico de webhook de MercadoPago"""
    return {
        "action": "payment.updated",
        "api_version": "v1",
        "data": {
            "id": "123456789"
        },
        "date_created": "2025-09-28T12:00:00.000-04:00",
        "id": fake.random_int(min=100000, max=999999),
        "live_mode": False,
        "type": "payment",
        "user_id": fake.random_int(min=100000000, max=999999999)
    }


# ===== MOCKS DE SERVICIOS EXTERNOS =====

@pytest.fixture
def mock_mercadopago_sdk():
    """Mock completo del SDK de MercadoPago"""
    with patch('mercadopago.SDK') as mock_sdk:
        # ✅ Configurar respuestas típicas
        mock_instance = Mock()
        mock_sdk.return_value = mock_instance
        
        # Mock payment.get()
        mock_instance.payment.return_value.get.return_value = {
            "body": {
                "id": 123456789,
                "status": "approved",
                "transaction_amount": 10.0,
                "description": "Test payment",
                "payer": {"email": "test@example.com"}
            },
            "status": 200
        }
        
        # Mock preference.create()
        mock_instance.preference.return_value.create.return_value = {
            "body": {
                "id": "preference_123",
                "init_point": "https://mercadopago.com/checkout/v1/redirect?pref_id=preference_123"
            },
            "status": 201
        }
        
        yield mock_instance


@pytest.fixture
def mock_auth_service():
    """Mock del servicio de autenticación de usuarios"""
    with patch('httpx.post') as mock_post, \
         patch('httpx.get') as mock_get:
        
        # ✅ Mock respuesta de validación de token
        mock_get.return_value.json.return_value = {
            "valid": True,
            "user_id": 1,
            "email": "test@example.com"
        }
        mock_get.return_value.status_code = 200
        
        # ✅ Mock respuesta de actualización de créditos
        mock_post.return_value.json.return_value = {
            "success": True,
            "new_credits": 150
        }
        mock_post.return_value.status_code = 200
        
        yield {"get": mock_get, "post": mock_post}


# ===== FIXTURES DE CONTEXTO GRAPHQL =====

@pytest.fixture
def graphql_context(test_db):
    """Contexto GraphQL con base de datos de pruebas"""
    return {
        "db": test_db,
        "request": Mock()  # Mock request si se necesita
    }


@pytest.fixture
def mock_info(graphql_context):
    """Mock del objeto Info de GraphQL"""
    info_mock = Mock()
    info_mock.context = graphql_context
    return info_mock


# ===== HELPERS PARA PRUEBAS =====

@pytest.fixture
def create_test_transaction(test_db, sample_credit_transaction_data):
    """Helper para crear transacciones de prueba en BD"""
    def _create_transaction(**kwargs):
        # ✅ Merge de datos por defecto con custom
        data = {**sample_credit_transaction_data, **kwargs}
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        return transaction
    
    return _create_transaction


@pytest.fixture
def assert_transaction_in_db(test_db):
    """Helper para verificar transacciones en BD"""
    def _assert_transaction(**filters):
        transaction = test_db.query(CreditTransaction).filter_by(**filters).first()
        assert transaction is not None, f"Transaction not found with filters: {filters}"
        return transaction
    
    return _assert_transaction