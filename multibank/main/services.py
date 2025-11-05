import requests
from django.utils import timezone
from datetime import datetime, timedelta
import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

class BankTokenManager:
    def __init__(self, target_bank, requesting_bank):
        self.target_bank = target_bank
        self.requesting_bank = requesting_bank
    
    def get_bank_token(self, force_refresh=False):
        """Получение или обновление банковского токена"""
        if not force_refresh and self.target_bank.is_token_valid():
            return self.target_bank.bank_token
        
        # Запрашиваем новый токен
        token_data = self._request_new_token()
        if token_data:
            self._save_token(token_data)
            return token_data['access_token']
        return None
    
    def _request_new_token(self):
        """Запрос нового банковского токена"""
        try:
            response = requests.post(
                self.target_bank.auth_url,
                params={
                    'client_id': self.requesting_bank.client_id,
                    'client_secret': self.requesting_bank.client_secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error getting bank token from {self.target_bank.name}: {e}")
            return None
    
    def _save_token(self, token_data):
        """Сохранение токена в базу"""
        expires_in = token_data.get('expires_in', 86400)
        self.target_bank.bank_token = token_data['access_token']
        self.target_bank.token_expires = timezone.now() + timedelta(seconds=expires_in)
        self.target_bank.save()
    
    def verify_token(self, token):
        """Верификация JWT токена с помощью публичного ключа банка"""
        try:
            # Получаем публичный ключ банка
            jwks_url = f"{self.target_bank.api_base_url}/.well-known/jwks.json"
            jwks_response = requests.get(jwks_url)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()


            kid = jwt.decode_header(token)["kid"]
            key = jwks.find_by_kid(kid)
            if not key:
                raise ValueError(f"Key with kide-{kid} not found in JWKS")
         
            decoded_token = jwt.decode(
                token, 
                key,
                options={"verify_signature": False}
            )
            decoded_token.validate()
            return decoded_token
        except Exception as e:
            print(f"Token verification error: {e}")
            return None
