from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.webpay.webpay_plus.configuration import Configuration

# Configurar el ambiente de prueba
Configuration.for_testing_webpay_plus()

tx = Transaction()
