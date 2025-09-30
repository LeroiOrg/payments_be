"""
Pruebas unitarias para Payment Service
- Lógica de procesamiento de pagos
- Integración con MercadoPago (mockeada)
- Manejo de errores del servicio
- Validación de datos
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.payment_service import MercadoPagoService


class TestMercadoPagoService:
    """Pruebas para el servicio de MercadoPago"""
    
    def test_init_con_token_valido(self):
        """✅ Debe inicializar correctamente con token válido"""
        # Arrange
        test_token = "TEST_TOKEN_123"
        
        # Act
        with patch('mercadopago.SDK') as mock_sdk:
            service = MercadoPagoService(access_token=test_token)
        
        # Assert
        assert service is not None
        mock_sdk.assert_called_once_with(test_token)
    
    def test_init_sin_token_falla(self):
        """❌ Debe fallar si no hay token configurado"""
        # Arrange - sin token ni variable de entorno
        with patch.dict('os.environ', {}, clear=True):
            # Act & Assert
            with pytest.raises(RuntimeError, match="MP_ACCESS_TOKEN no configurado"):
                MercadoPagoService(access_token=None)
    
    def test_init_usa_variable_entorno(self):
        """✅ Debe usar token de variable de entorno si no se pasa explícito"""
        # Arrange
        env_token = "ENV_TOKEN_456"
        
        with patch.dict('os.environ', {'MP_ACCESS_TOKEN': env_token}):
            with patch('mercadopago.SDK') as mock_sdk:
                # Act
                service = MercadoPagoService()
        
        # Assert
        mock_sdk.assert_called_once_with(env_token)
    
    @patch('mercadopago.SDK')
    def test_create_preference_exitosa(self, mock_sdk_class):
        """✅ Debe crear preferencia de pago correctamente"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        # Respuesta simulada de MercadoPago
        expected_response = {
            "body": {
                "id": "preference_123456",
                "init_point": "https://mercadopago.com/checkout/v1/redirect?pref_id=preference_123456",
                "sandbox_init_point": "https://sandbox.mercadopago.com/checkout/v1/redirect?pref_id=preference_123456"
            },
            "status": 201
        }
        mock_preference.create.return_value = expected_response
        
        preference_data = {
            "items": [
                {
                    "title": "Créditos LEROI",
                    "quantity": 1,
                    "unit_price": 10.0,
                    "currency_id": "USD"
                }
            ],
            "back_urls": {
                "success": "http://localhost:5173/pricing/success",
                "failure": "http://localhost:5173/pricing/failure",
                "pending": "http://localhost:5173/pricing/pending"
            }
        }
        
        service = MercadoPagoService(access_token="test_token")
        
        # Act
        result = service.create_preference(preference_data)
        
        # Assert
        assert result == expected_response
        mock_preference.create.assert_called_once_with(preference_data)
    
    @patch('mercadopago.SDK')
    def test_create_preference_datos_invalidos(self, mock_sdk_class):
        """❌ Debe manejar error con datos inválidos"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        # Simular respuesta de error
        error_response = {
            "body": {
                "message": "Invalid request data",
                "error": "bad_request",
                "cause": [
                    {
                        "code": "invalid_parameter",
                        "description": "items is required"
                    }
                ]
            },
            "status": 400
        }
        mock_preference.create.return_value = error_response
        
        service = MercadoPagoService(access_token="test_token")
        preference_invalida = {}  # Sin items requeridos
        
        # Act
        result = service.create_preference(preference_invalida)
        
        # Assert
        assert result["status"] == 400
        assert "error" in result["body"]
        mock_preference.create.assert_called_once_with(preference_invalida)
    
    @patch('mercadopago.SDK')
    def test_create_preference_error_red(self, mock_sdk_class):
        """❌ Debe manejar errores de red/conexión"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        # Simular error de conexión
        mock_preference.create.side_effect = Exception("Connection error")
        
        service = MercadoPagoService(access_token="test_token")
        preference_data = {"items": [{"title": "Test", "quantity": 1, "unit_price": 10}]}
        
        # Act & Assert
        with pytest.raises(Exception, match="Connection error"):
            service.create_preference(preference_data)
    
    @patch('mercadopago.SDK')
    def test_preference_con_external_reference(self, mock_sdk_class):
        """✅ Debe incluir external_reference correctamente"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        expected_response = {"body": {"id": "pref_with_ref"}, "status": 201}
        mock_preference.create.return_value = expected_response
        
        service = MercadoPagoService(access_token="test_token")
        
        preference_data = {
            "items": [{"title": "Test Credits", "quantity": 1, "unit_price": 15.0}],
            "external_reference": '{"sessionId": "session_123", "userId": 456}'
        }
        
        # Act
        result = service.create_preference(preference_data)
        
        # Assert
        assert result["status"] == 201
        
        # Verificar que external_reference se pasó correctamente
        call_args = mock_preference.create.call_args[0][0]
        assert "external_reference" in call_args
        assert "session_123" in call_args["external_reference"]
    
    @patch('mercadopago.SDK')
    def test_preference_con_back_urls_personalizadas(self, mock_sdk_class):
        """✅ Debe configurar URLs de retorno personalizadas"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        mock_preference.create.return_value = {"body": {"id": "pref_urls"}, "status": 201}
        
        service = MercadoPagoService(access_token="test_token")
        
        custom_urls = {
            "success": "https://miapp.com/success",
            "failure": "https://miapp.com/failure", 
            "pending": "https://miapp.com/pending"
        }
        
        preference_data = {
            "items": [{"title": "Premium Credits", "quantity": 1, "unit_price": 25.0}],
            "back_urls": custom_urls,
            "auto_return": "approved"
        }
        
        # Act
        result = service.create_preference(preference_data)
        
        # Assert
        assert result["status"] == 201
        
        # Verificar URLs personalizadas
        call_args = mock_preference.create.call_args[0][0]
        assert call_args["back_urls"] == custom_urls
        assert call_args["auto_return"] == "approved"
    
    @patch('mercadopago.SDK')
    def test_multiples_items_en_preference(self, mock_sdk_class):
        """✅ Debe manejar múltiples items en una preferencia"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_preference = Mock()
        mock_sdk_instance.preference.return_value = mock_preference
        mock_sdk_class.return_value = mock_sdk_instance
        
        mock_preference.create.return_value = {"body": {"id": "pref_multiple"}, "status": 201}
        
        service = MercadoPagoService(access_token="test_token")
        
        preference_data = {
            "items": [
                {
                    "title": "Paquete Básico - 100 Créditos",
                    "quantity": 1,
                    "unit_price": 5.0,
                    "currency_id": "USD"
                },
                {
                    "title": "Paquete Premium - 500 Créditos",
                    "quantity": 1, 
                    "unit_price": 20.0,
                    "currency_id": "USD"
                }
            ]
        }
        
        # Act
        result = service.create_preference(preference_data)
        
        # Assert
        assert result["status"] == 201
        
        # Verificar que se pasaron múltiples items
        call_args = mock_preference.create.call_args[0][0]
        assert len(call_args["items"]) == 2
        assert call_args["items"][0]["title"] == "Paquete Básico - 100 Créditos"
        assert call_args["items"][1]["title"] == "Paquete Premium - 500 Créditos"
    
    @patch('mercadopago.SDK')
    def test_sdk_inicializado_una_sola_vez(self, mock_sdk_class):
        """✅ SDK debe inicializarse solo una vez por instancia"""
        # Arrange
        mock_sdk_instance = Mock()
        mock_sdk_class.return_value = mock_sdk_instance
        
        # Act - crear servicio y hacer múltiples operaciones
        service = MercadoPagoService(access_token="test_token")
        service.create_preference({"items": [{"title": "Test 1", "quantity": 1, "unit_price": 10}]})
        service.create_preference({"items": [{"title": "Test 2", "quantity": 1, "unit_price": 15}]})
        
        # Assert - SDK debe haberse inicializado solo una vez
        assert mock_sdk_class.call_count == 1
        mock_sdk_class.assert_called_with("test_token")
    
    def test_token_override_sobre_env_var(self):
        """✅ Token explícito debe tener prioridad sobre variable de entorno"""
        # Arrange
        env_token = "ENV_TOKEN"
        explicit_token = "EXPLICIT_TOKEN"
        
        with patch.dict('os.environ', {'MP_ACCESS_TOKEN': env_token}):
            with patch('mercadopago.SDK') as mock_sdk:
                # Act
                service = MercadoPagoService(access_token=explicit_token)
        
        # Assert
        mock_sdk.assert_called_once_with(explicit_token)  # No el de ENV