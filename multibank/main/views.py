from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from .services.financial_aggregator import FinancialAggregator
from .services import BankTokenManager
from .models import BankConsent, TargetBank, RequestingBank
import requests

@login_required
def dashboard(request):
    """Главная страница с агрегированными данными"""
    aggregator = FinancialAggregator(request.user)
    financial_data = aggregator.aggregate_all_data()
    
    context = {
        'total_balance': f"{financial_data['total_balance']:,.2f}",
        'total_accounts': financial_data['total_accounts'],
        'banks_connected': financial_data['banks_connected'],
        'accounts': financial_data['accounts']
    }
    
    return render(request, 'front/dashboard.html', context)

@login_required
def create_consent(request, bank_id):
    """Создание согласия для доступа к данным банка"""
    target_bank = TargetBank.objects.get(id=bank_id)
    requesting_bank = RequestingBank.objects.first()
    
    # Получаем банковский токен
    token_manager = BankTokenManager(target_bank, requesting_bank)
    bank_token = token_manager.get_bank_token()
    
    if not bank_token:
        return JsonResponse({'error': 'Cannot get bank token'}, status=400)
    
    # Создаем запрос согласия
    consent_url = f"{target_bank.api_base_url}/account-consents"
    headers = {
        'Authorization': f'Bearer {bank_token}',
        'X-Requesting-Bank': requesting_bank.client_id,
        'Content-Type': 'application/json'
    }
    
    # client_id клиента в целевом банке (нужно получить от пользователя)
    client_id = request.POST.get('client_id', f'user_{request.user.id}')
    
    consent_data = {
        'client_id': client_id,
        'permissions': ['accounts', 'transactions', 'balances'],
        'expires_in': 3600
    }
    
    try:
        response = requests.post(consent_url, json=consent_data, headers=headers)
        response.raise_for_status()
        consent_response = response.json()
        
        # Сохраняем согласие
        BankConsent.objects.create(
            user=request.user,
            target_bank=target_bank,
            consent_id=consent_response['consent_id'],
            client_id=client_id,
            status='PENDING',  # Пользователь должен подтвердить в банке
            expires_at=timezone.now() + timedelta(hours=1)
        )
        
        # Возвращаем URL для подтверждения согласия пользователем
        consent_approval_url = consent_response.get('approval_url')
        
        return JsonResponse({
            'consent_id': consent_response['consent_id'],
            'approval_url': consent_approval_url,
            'status': 'pending_approval'
        })
        
    except requests.exceptions.RequestException as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def refresh_tokens(request):
    """Принудительное обновление всех банковских токенов"""
    target_banks = TargetBank.objects.all()
    requesting_bank = RequestingBank.objects.first()
    
    updated_tokens = 0
    for target_bank in target_banks:
        token_manager = BankTokenManager(target_bank, requesting_bank)
        if token_manager.get_bank_token(force_refresh=True):
            updated_tokens += 1
    
    return JsonResponse({'tokens_updated': updated_tokens})



