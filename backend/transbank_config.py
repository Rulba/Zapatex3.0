# transbank_config.py (versión simulada)

from datetime import datetime

class RespuestaSimulada:
    def __init__(self, token, url):
        self.token = token
        self.url = url

class ResultadoPagoSimulado:
    def __init__(self):
        self.status = 'AUTHORIZED'
        self.amount = 10000
        self.buy_order = 'SIMULATED_ORDER'
        self.session_id = 'SIMULATED_SESSION'
        self.authorization_code = 'SIM123'
        self.payment_type_code = 'VN'
        self.response_code = 0
        self.installments_number = 0
        self.card_detail = {'card_number': '**** **** **** 1234'}

class TransaccionSimulada:
    def create(self, buy_order, session_id, amount, return_url):
        print(f"[Simulación] Creando transacción: {buy_order} - ${amount}")
        return RespuestaSimulada(
            token="SIMULATED_TOKEN_" + str(int(datetime.utcnow().timestamp())),
            url=return_url  # Podés redirigir directamente a resultado_pago
        )

    def commit(self, token_ws):
        print(f"[Simulación] Confirmando transacción con token: {token_ws}")
        return ResultadoPagoSimulado()

tx = TransaccionSimulada()
