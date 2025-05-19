from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.integration_type import IntegrationType
from transbank.webpay.webpay_plus.configuration import Configuration

# Credenciales de prueba
commerce_code = '597055555532'  # código de comercio de pruebas
api_key = '1234567890'

# Configurar Webpay Plus en modo sandbox
configuration = Configuration()
configuration.commerce_code = commerce_code
configuration.api_key = api_key
configuration.integration_type = IntegrationType.TEST

# Instancia de Transacción
tx = Transaction(configuration=configuration)
