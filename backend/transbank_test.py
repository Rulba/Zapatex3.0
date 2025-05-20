from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

tx = Transaction(WebpayOptions(
    commerce_code='597055555532',
    api_key='Xcb9JYxJfS4lOxU6I4GhJ1t3sTLI9VSn',
    integration_type=IntegrationType.TEST
))

buy_order = "orden-test-1234"
session_id = "sesion-test-5678"
amount = 1000
return_url = "http://127.0.0.1:5000/resultado_pago"

try:
    response = tx.create(buy_order, session_id, amount, return_url)
    print("✅ Transbank respondió:")
    print("URL:", response.get("url"))
    print("Token:", response.get("token"))
except Exception as e:
    print("❌ Error al crear transacción:", e)
