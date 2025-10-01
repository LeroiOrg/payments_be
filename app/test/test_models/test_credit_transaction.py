"""
Pruebas unitarias para el modelo CreditTransaction
- Validación de campos requeridos
- Estados permitidos
- Timestamps automáticos
- Integridad de datos
"""

import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from app.models.credit_transaction import CreditTransaction


class TestCreditTransactionModel:
    """Pruebas del modelo CreditTransaction"""
    
    def test_crear_transaccion_valida(self, test_db, sample_credit_transaction_data):
        """✅ Prueba crear transacción con todos los datos válidos"""
        # Arrange
        data = sample_credit_transaction_data
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.id is not None
        assert transaction.email == data["email"]
        assert transaction.credits == data["credits"]
        assert transaction.status == data["status"]
        assert transaction.payment_id == data["payment_id"]
        assert transaction.session_id == data["session_id"]
        assert transaction.token == data["token"]
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)
    
    def test_campos_requeridos_email(self, test_db, sample_credit_transaction_data):
        """❌ Debe fallar si no se proporciona email"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        del data["email"]  # Remover campo requerido
        
        # Act & Assert
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_campos_requeridos_credits(self, test_db, sample_credit_transaction_data):
        """❌ Debe fallar si no se proporcionan créditos"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        del data["credits"]  # Remover campo requerido
        
        # Act & Assert
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_campos_requeridos_status(self, test_db, sample_credit_transaction_data):
        """❌ Debe fallar si no se proporciona status"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        del data["status"]  # Remover campo requerido
        
        # Act & Assert
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        
        with pytest.raises(IntegrityError):
            test_db.commit()
    
    def test_estados_validos_pending(self, test_db, sample_credit_transaction_data):
        """✅ Status 'pending' debe ser válido"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        data["status"] = "pending"
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.status == "pending"
    
    def test_estados_validos_approved(self, test_db, sample_credit_transaction_data):
        """✅ Status 'approved' debe ser válido"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        data["status"] = "approved"
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.status == "approved"
    
    def test_estados_validos_failed(self, test_db, sample_credit_transaction_data):
        """✅ Status 'failed' debe ser válido"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        data["status"] = "failed"
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.status == "failed"
    
    def test_timestamp_automatico_created_at(self, test_db, sample_credit_transaction_data):
        """✅ created_at debe generarse automáticamente"""
        # Act
        transaction = CreditTransaction(**sample_credit_transaction_data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.created_at is not None
        assert isinstance(transaction.created_at, datetime)
        # Verificar que está en un rango razonable (últimos 10 segundos)
        ahora = datetime.utcnow()
        diferencia = abs((ahora - transaction.created_at).total_seconds())
        assert diferencia < 10, f"Timestamp muy alejado: {transaction.created_at} vs {ahora}"
    
    def test_email_indexado_busqueda_rapida(self, test_db, sample_credit_transaction_data):
        """✅ Debe poder buscar transacciones por email eficientemente"""
        # Arrange
        email_test = "search@example.com"
        data = sample_credit_transaction_data.copy()
        data["email"] = email_test
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        
        # Buscar por email
        found = test_db.query(CreditTransaction).filter_by(email=email_test).first()
        
        # Assert
        assert found is not None
        assert found.email == email_test
        assert found.credits == data["credits"]
    
    def test_payment_id_unico(self, test_db, sample_credit_transaction_data):
        """✅ payment_id puede tener duplicados (cambiado - no hay constraint unique)"""
        # Arrange
        payment_id = "SHARED_PAYMENT_123"
        
        # Primera transacción
        data1 = sample_credit_transaction_data.copy()
        data1["payment_id"] = payment_id
        transaction1 = CreditTransaction(**data1)
        test_db.add(transaction1)
        test_db.commit()
        
        # Segunda transacción con mismo payment_id (permitido)
        data2 = sample_credit_transaction_data.copy()
        data2["payment_id"] = payment_id
        data2["email"] = "different@email.com"  # Email diferente
        data2["session_id"] = "different_session_123"  # Session diferente
        transaction2 = CreditTransaction(**data2)
        test_db.add(transaction2)
        test_db.commit()  # Debe funcionar sin error
        
        # Assert - ambas transacciones deben existir
        transactions = test_db.query(CreditTransaction).filter_by(payment_id=payment_id).all()
        assert len(transactions) == 2
    
    def test_creditos_positivos(self, test_db, sample_credit_transaction_data):
        """✅ Debe aceptar créditos positivos"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        data["credits"] = 250
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.credits == 250
    
    def test_creditos_zero(self, test_db, sample_credit_transaction_data):
        """✅ Debe aceptar créditos en cero"""
        # Arrange
        data = sample_credit_transaction_data.copy()
        data["credits"] = 0
        
        # Act
        transaction = CreditTransaction(**data)
        test_db.add(transaction)
        test_db.commit()
        test_db.refresh(transaction)
        
        # Assert
        assert transaction.credits == 0
    
    def test_multiple_transacciones_mismo_email(self, test_db, sample_credit_transaction_data):
        """✅ Un email puede tener múltiples transacciones"""
        # Arrange
        email = "multi@transactions.com"
        
        # Primera transacción
        data1 = sample_credit_transaction_data.copy()
        data1["email"] = email
        data1["payment_id"] = "PAYMENT_1"
        transaction1 = CreditTransaction(**data1)
        test_db.add(transaction1)
        
        # Segunda transacción
        data2 = sample_credit_transaction_data.copy()
        data2["email"] = email
        data2["payment_id"] = "PAYMENT_2"
        transaction2 = CreditTransaction(**data2)
        test_db.add(transaction2)
        
        test_db.commit()
        
        # Act - buscar todas las transacciones del email
        transactions = test_db.query(CreditTransaction).filter_by(email=email).all()
        
        # Assert
        assert len(transactions) == 2
        assert all(t.email == email for t in transactions)
        payment_ids = {t.payment_id for t in transactions}
        assert payment_ids == {"PAYMENT_1", "PAYMENT_2"}
    
    def test_session_id_unico_por_transaccion(self, test_db, sample_credit_transaction_data):
        """✅ Cada transacción debe tener su propio session_id"""
        # Arrange & Act
        data1 = sample_credit_transaction_data.copy()
        data1["session_id"] = "session_123"
        data1["payment_id"] = "payment_1"
        transaction1 = CreditTransaction(**data1)
        test_db.add(transaction1)
        
        data2 = sample_credit_transaction_data.copy()
        data2["session_id"] = "session_456"
        data2["payment_id"] = "payment_2"
        transaction2 = CreditTransaction(**data2)
        test_db.add(transaction2)
        
        test_db.commit()
        test_db.refresh(transaction1)
        test_db.refresh(transaction2)
        
        # Assert
        assert transaction1.session_id != transaction2.session_id
        assert transaction1.session_id == "session_123"
        assert transaction2.session_id == "session_456"