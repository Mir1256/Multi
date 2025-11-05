from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta

class RequestingBank(models.Model):
    """Ваш банк (команда) как запрашивающая сторона"""
    name = models.CharField(max_length=100)
    client_id = models.CharField(max_length=100)  # код вашей команды
    client_secret = models.CharField(max_length=255)  # ваш API key
    
    def __str__(self):
        return self.name

class TargetBank(models.Model):
    """Банки, к которым делаем запросы"""
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)  # VBank, ABank, SBank
    auth_url = models.URLField()  # https://vbank.open.bankingapi.ru/auth/bank-token
    api_base_url = models.URLField()  # базовый URL API банка
    bank_token = models.TextField(blank=True)  # токен для этого банка
    token_expires = models.DateTimeField(null=True, blank=True)
    
    def is_token_valid(self):
        return self.token_expires and self.token_expires > datetime.now() # Глянуть!!!
    
    def __str__(self):
        return self.name

class BankConsent(models.Model):
    """Согласия для межбанковского доступа"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    target_bank = models.ForeignKey(TargetBank, on_delete=models.CASCADE)
    consent_id = models.CharField(max_length=255)
    client_id = models.CharField(max_length=100)  # client_id клиента в целевом банке
    status = models.CharField(max_length=50, choices=[
        ('PENDING', 'Ожидает подтверждения'),
        ('APPROVED', 'Подтверждено'),
        ('REJECTED', 'Отклонено'),
        ('EXPIRED', 'Истекло')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        unique_together = ['user', 'target_bank']
