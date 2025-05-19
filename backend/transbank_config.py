from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType

# Configuración global
Transaction.commerce_code = '597055555532'
Transaction.api_key = '1234567890'
Transaction.integration_type = IntegrationType.TEST

tx = Transaction()
