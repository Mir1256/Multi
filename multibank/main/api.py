import requests
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from services import BankTokenManager

class ApiClient:
    def __init__(self, user):
        self.user = user
        self.requesting_bank = RequestingBank.objects.first()
        self.target_banks = TargetBank.objects.all()
    
    def aggregate_all_data(self):
        """Агрегация данных из всех банков"""
        total_data = {
            'total_balance': 0,
            'total_accounts': 0,
            'total_income': 0,
            'total_expenses': 0,
            'accounts': [],
            'banks_connected': 0
        }
        
        for target_bank in self.target_banks:
            bank_data = self._get_bank_data(target_bank)
            if bank_data:
                self._merge_data(total_data, bank_data)
                total_data['banks_connected'] += 1
        
        return total_data
    
    def _get_bank_data(self, target_bank):
        """Получение данных из конкретного банка"""
        try:
            # Получаем банковский токен
            token_manager = BankTokenManager(target_bank, self.requesting_bank)
            bank_token = token_manager.get_bank_token()
            
            if not bank_token:
                print(f"No token for {target_bank.name}")
                return None
            
            # Проверяем есть ли согласие для межбанкового запроса
            consent = BankConsent.objects.filter(
                user=self.user,
                target_bank=target_bank,
                status='APPROVED',
                expires_at__gt=timezone.now()
            ).first()
            
            if consent:
                # Межбанковый запрос с согласием
                return self._make_interbank_request(target_bank, bank_token, consent)
            else:
                # Пробуем запросить свои счета (если пользователь этого банка)
                return self._make_own_bank_request(target_bank, bank_token)
                
        except Exception as e:
            print(f"Error getting data from {target_bank.name}: {e}")
            return None
    
    def _make_interbank_request(self, target_bank, bank_token, consent):
        """Межбанковый запрос с согласием"""
        headers = {
            'Authorization': f'Bearer {bank_token}',
            'X-Requesting-Bank': self.requesting_bank.client_id,
            'X-Consent-Id': consent.consent_id,
            'Content-Type': 'application/json'
        }
        
        # Запрос счетов
        accounts_url = f"{target_bank.api_base_url}/accounts"
        response = requests.get(accounts_url, headers=headers)
        
        if response.status_code == 200:
            accounts_data = response.json()
            return self._process_accounts_data(accounts_data, target_bank.name)
        
        return None
    
    def _make_own_bank_request(self, target_bank, bank_token):
        """Запрос своих счетов (если пользователь этого банка)"""
        headers = {
            'Authorization': f'Bearer {bank_token}',
            'Content-Type': 'application/json'
        }
        
        # Здесь нужно понять, как аутентифицировать конкретного пользователя
        # Возможно через дополнительные параметры или заголовки
        accounts_url = f"{target_bank.api_base_url}/accounts"
        response = requests.get(accounts_url, headers=headers)
        
        if response.status_code == 200:
            accounts_data = response.json()
            return self._process_accounts_data(accounts_data, target_bank.name)
        
        return None
    
    def _process_accounts_data(self, accounts_data, bank_name):
        """Обработка данных счетов"""
        if not accounts_data or 'accounts' not in accounts_data:
            return None
        
        processed_data = {
            'total_balance': 0,
            'total_accounts': 0,
            'accounts': []
        }
        
        for account in accounts_data['accounts']:
            balance = self._extract_balance(account)
            
            processed_data['total_balance'] += balance
            processed_data['total_accounts'] += 1
            
            processed_data['accounts'].append({
                'bank': bank_name,
                'account_id': account.get('account_id'),
                'balance': balance,
                'currency': account.get('currency', 'RUB'),
                'type': account.get('account_type'),
                'nickname': account.get('nickname'),
                'servicer': account.get('servicer', {})
            })
        
        return processed_data
    
    def _extract_balance(self, account_data):
        """Извлечение баланса из данных счета"""
        # Адаптируй под реальную структуру ответа банков
        if 'balance' in account_data and 'amount' in account_data['balance']:
            return float(account_data['balance']['amount'])
        return 0.0
    
    def _merge_data(self, total_data, new_data):
        """Объединение данных"""
        total_data['total_balance'] += new_data['total_balance']
        total_data['total_accounts'] += new_data['total_accounts']
        total_data['accounts'].extend(new_data['accounts'])

    def _create_new_account(self,accept):
        base_api_url = self.target_banks.filter()


    