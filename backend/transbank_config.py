from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.webpay.webpay_plus.webpay_plus_options import WebpayPlusOptions
from transbank.common.integration_type import IntegrationType

# Configuración para entorno de pruebas
tx = Transaction(
    options=WebpayPlusOptions(
        commerce_code='597055555532',
        api_key='Xcb9JYxJfS4lOxU6I4GhJ1t3sTLI9VSn',
        integration_type=IntegrationType.TEST
    )
)
