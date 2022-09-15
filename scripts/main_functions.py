#system libs
import decimal
import time
#scripts libs
from scripts.vars import vars
from scripts.core_functions import core_functions

class main_functions:

    #RESUMO: tenta efetuar a troca do 'token_from' por 'token_to' através da DEX pancakeswap até conseguir
    def LaunchBuy(token_to, amount, token_from = vars.wbnb_contract, wallet_pvk = vars.my_wallet_pvk, slippage = vars.slippage, gas_limit = vars.gas_limit, gas_price = vars.gas_price, seconds_deadline = vars.seconds_deadline, usd_maxfee = vars.usd_maxfee, max_priority = False, ignore_fee = False):
        while True:
            if core_functions.GetTokenPrice(token_to)["is_token_listed"] == True:
                print(main_functions.SystemTimeLog() + " : " + "listado")
                main_functions.Trade(token_from, amount, token_to, wallet_pvk, slippage, gas_limit, gas_price, seconds_deadline, usd_maxfee, max_priority, ignore_fee)
            else:
                print(main_functions.SystemTimeLog() + " : " + " não esta listado")

    #RESUMO: efetua a troca do 'token_from' por 'token_to' através da DEX pancakeswap
    def Trade(token_from, amount, token_to, wallet_pvk = vars.my_wallet_pvk, slippage = vars.slippage, gas_limit = vars.gas_limit, gas_price = vars.gas_price, seconds_deadline = vars.seconds_deadline, usd_maxfee = vars.usd_maxfee, max_priority = False, ignore_fee = False):
        if token_from == vars.wbnb_contract:
            signed_txh = core_functions.BuyToken(token_to, decimal.Decimal(str(amount)), wallet_pvk, slippage, gas_limit, gas_price, seconds_deadline)
        elif token_to == vars.wbnb_contract:
            signed_txh = core_functions.SellToken(token_from, decimal.Decimal(str(amount)), wallet_pvk, slippage, gas_limit, gas_price, seconds_deadline)
        else:
            signed_txh = core_functions.TradeToken(token_from, decimal.Decimal(str(amount)), token_to, wallet_pvk, slippage, gas_limit, gas_price, seconds_deadline)
        if type(signed_txh) != dict:
            return signed_txh
        if max_priority == True:
            max_priority_signed_txh = core_functions.SetTransactionFee(signed_txh["signed_txh"], usd_maxfee)
            if max_priority_signed_txh != "ERROR":
                signed_txh = max_priority_signed_txh
        if ignore_fee == False:
            user_response = main_functions.UserConfirm(main_functions.FeeConfirmStr(signed_txh["estimate_usdfee"]))
            if user_response != "USER ACCEPT":
                return user_response
        transaction_txh = core_functions.SubmitTransaction(signed_txh["signed_txh"])
        return transaction_txh

    #RESUMO: realiza allowance (permissão) de um 'token_address' para um 'allowance_address'
    def Approve(token_address, spender_address = vars.pancakeswap_router_address, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price, balance_to_allow = "infinity", ignore_fee = False):
        signed_txh = core_functions.Approve(token_address, spender_address, wallet_pvk, gas_limit, gas_price, balance_to_allow)
        if type(signed_txh) != dict:
            return signed_txh
        if ignore_fee == False:
            user_response = main_functions.UserConfirm(main_functions.FeeConfirmStr(signed_txh["estimate_usdfee"]))
            if user_response != "USER ACCEPT":
                return user_response
        transaction_txh = core_functions.SubmitTransaction(signed_txh["signed_txh"])
        return transaction_txh

    #RESUMO: realiza allowance (permissão) de um 'token_address' para um 'allowance_address' de valor NULO
    def Revoke(token_address, spender_address = vars.pancakeswap_router_address, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price, ignore_fee = False):
        signed_txh = core_functions.Approve(token_address, spender_address, wallet_pvk, gas_limit, gas_price, 0)
        if type(signed_txh) != dict:
            return signed_txh
        if ignore_fee == False:
            user_response = main_functions.UserConfirm(main_functions.FeeConfirmStr(signed_txh["estimate_usdfee"]))
            if user_response != "USER ACCEPT":
                return user_response
        transaction_txh = core_functions.SubmitTransaction(signed_txh["signed_txh"])
        return transaction_txh

    #RESUMO: realiza uma transferência
    def Transfer(token_address, to_wallet, amount, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price, ignore_fee = False):
        if token_address == vars.wbnb_contract:
            signed_txh = core_functions.TransferBNB(to_wallet, decimal.Decimal(str(amount)), wallet_pvk, gas_limit, gas_price)
        else:
            signed_txh = core_functions.TransferToken(token_address, to_wallet, decimal.Decimal(str(amount)), wallet_pvk, gas_limit, gas_price)
        if type(signed_txh) != dict:
            return signed_txh
        if ignore_fee == False:
            user_response = main_functions.UserConfirm(main_functions.FeeConfirmStr(signed_txh["estimate_usdfee"]))
            if user_response != "USER ACCEPT":
                return user_response
        transaction_txh = core_functions.SubmitTransaction(signed_txh["signed_txh"])
        return transaction_txh

    #RESUMO: aplica retorno apenas quando a transação é finalizada
    def WaitTransactionStatus(txh, log = False, sleep_time = 0.5, max_time = 180):
        total_time = 0
        while total_time < max_time:
            status_result = core_functions.GetTransactionStatus(txh)
            if status_result == 1:
                if log == True:
                    print(f"{main_functions.SystemTimeLog()} = found ({status_result})")
                return status_result
            else:
                if log == True:
                    print(f"{main_functions.SystemTimeLog()} = not found yet ({status_result})")
                time.sleep(sleep_time)
                total_time += sleep_time
        return "MAX TIME EXCEED"

    #RESUMO: exige uma confirmação do usuário
    def UserConfirm(str_to_confirm):
        user_response = ""
        while user_response != "USER ACCEPT":
            user_response = str(input("{0} (y = yes, n = no): ".format(str(str_to_confirm))))
            if user_response == "y":
                return "USER ACCEPT"
            elif user_response == "n":
                return "USER DID NOT ACCEPT"
        else:
            print("WRONG USER INPUT")

    #RESUMO: cria uma string para exigir confirmação da taxa de transação
    def FeeConfirmStr(amount):
        if amount == 0:
            confirmation_str = "Confirm fee amount ('no estimation')"
        else:
            confirmation_str = "Confirm fee amount ({0} usd)".format(round(amount, 2))
        return confirmation_str

    #RESUMO: horario do sistema
    def SystemTimeLog():
        return str(time.strftime("%d/%b at %H:%M:%S"))
