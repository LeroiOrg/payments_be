import os
import mercadopago
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()  # fuerza a cargar el .env al instanciar el servicio

class MercadoPagoService:
    def __init__(self, access_token: str | None = None):
        token = access_token or os.getenv("MP_ACCESS_TOKEN")
        if not token:
            raise RuntimeError("MP_ACCESS_TOKEN no configurado")
        self.sdk = mercadopago.SDK(token)

    def create_preference(self, preference_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        preference_data: diccionario según la API / SDK (items, back_urls, payer, etc.)
        Devuelve la respuesta cruda del SDK (incluye 'init_point' para Checkout tradicional)
        """
        resp = self.sdk.preference().create(preference_data)
        return resp
