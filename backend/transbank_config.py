from transbank.webpay.webpay_plus.transaction import Transaction
from transbank.webpay.webpay_plus.configuration import Configuration
from transbank.common.environment import Environment

Configuration.for_testing_webpay_plus()
tx = Transaction()
