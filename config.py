#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_IDS = [int(id.strip()) for id in os.getenv('ADMIN_IDS', '').split(',') if id.strip()]

# OKPAY Configuration
OKPAY_APP_ID = os.getenv('OKPAY_APP_ID')
OKPAY_SECRET = os.getenv('OKPAY_SECRET')
OKPAY_API_URL = os.getenv('OKPAY_API_URL', 'https://api.okaypay.me/shop/')

# Webhook Configuration
WEBHOOK_HOST = os.getenv('WEBHOOK_HOST', '')
WEBHOOK_PORT = int(os.getenv('WEBHOOK_PORT', 8443))
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH', '/webhook')

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./bookkeeping.db')

# Membership Pricing (in USDT)
MEMBERSHIP_PRICE_30_DAYS = float(os.getenv('MEMBERSHIP_PRICE_30_DAYS', 10))
MEMBERSHIP_PRICE_90_DAYS = float(os.getenv('MEMBERSHIP_PRICE_90_DAYS', 25))
MEMBERSHIP_PRICE_365_DAYS = float(os.getenv('MEMBERSHIP_PRICE_365_DAYS', 80))

# Supported Currencies
SUPPORTED_CURRENCIES = [
    'CNY', 'USD', 'JPY', 'EUR', 'GBP', 'HKD', 'KRW', 'SGD',
    'THB', 'PHP', 'MYR', 'IDR', 'VND', 'TWD', 'AUD', 'CAD',
    'NZD', 'CHF', 'SEK', 'DKK', 'NOK', 'RUB', 'INR', 'BRL',
    'MXN', 'ZAR', 'TRY', 'AED', 'SAR', 'USDT'
]

# Default Settings
DEFAULT_CURRENCY = 'CNY'
DEFAULT_EXCHANGE_RATE = 7.2
DEFAULT_FEE_RATE = 0.01

# Web Bill System Configuration
WEB_BILL_PORT = int(os.getenv('WEB_BILL_PORT', 52000))
WEB_BILL_HOST = os.getenv('WEB_BILL_HOST', '0.0.0.0')

# Web Admin System Configuration
WEB_ADMIN_PORT = int(os.getenv('WEB_ADMIN_PORT', 38888))
WEB_ADMIN_HOST = os.getenv('WEB_ADMIN_HOST', '0.0.0.0')
WEB_ADMIN_USERNAME = os.getenv('WEB_ADMIN_USERNAME', 'admin')
WEB_ADMIN_PASSWORD = os.getenv('WEB_ADMIN_PASSWORD', '123456')
