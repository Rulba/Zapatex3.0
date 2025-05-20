from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.common.options import WebpayOptions
from transbank.common.integration_type import IntegrationType

tx = Transaction(WebpayOptions(
    commerce_code='597055555532',
    api_key='Xcb9JYxJfS4lOxU6I4GhJ1t3sTLI9VSn',
    integration_type=IntegrationType.TEST
))
