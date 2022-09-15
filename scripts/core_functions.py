#system libs
from distutils import core
import time
import decimal
import requests
#script libs
from scripts.vars import vars
#pip libs
from eth_account import Account
import secrets

class core_functions:

    #lista de tarefas:
    #funcoes de trade devem chamar funcoes proprias de 'amount out min'
    #corrigir função estimateGas
    #criar função 'TransferFrom'
    #fazer vars.web3.toChecksumAddress(address) em todos os address
    #verificar se um contrato é scam: https://honeypot.api.rugdoc.io/api/honeypotStatus.js?address=${purchaseToken}&chain=bsc
    #pagar pela api da bscscan e criar função: GetLiquidityHolders

    #gas_price deve estar multiplicado a 10**9
    def EstimateGas(data, to_address, value, gas_price, gas_limit, bscscan_apikey = vars.bscscan_apikey):
        api_response = requests.get(f"https://api.bscscan.com/api?module=proxy&action=eth_estimateGas&data={str(hex(data))}&to={to_address}&value={str(hex(value))}&gasPrice={str(hex(gas_price))}&gas={str(hex(gas_limit))}&apikey={bscscan_apikey}").text
        print(api_response)

    #RESUMO: retorna o status de uma transação
    def GetTransactionStatus(txh, bscscan_apikey = vars.bscscan_apikey):
        try:
            api_response = int(requests.get(f"https://api.bscscan.com/api?module=transaction&action=gettxreceiptstatus&txhash={txh}&apikey={bscscan_apikey}").text.split(":")[4].replace('"', "").replace("}", ""))
            return api_response
        except Exception as e:
            print(f"error = {e}, txh = {txh}")
            return "ERROR"

    #RESUMO: retorna informações de uma transação JÁ FINALIZADA (erro caso não tenha finalizado)
    def GetTransactionInfo(txh, bscscan_apikey = vars.bscscan_apikey):
        status = core_functions.GetTransactionStatus(txh, bscscan_apikey)
        if status != 1:
            return "transação não finalizada"
        else:
            server_response_1 = vars.web3.eth.getTransactionReceipt(txh)
            server_response_2 = vars.web3.eth.getTransaction(txh)
            from_address = server_response_2["from"]
            to_address = server_response_2["to"]
            index_in_the_block = server_response_2["transactionIndex"]
            gas_limit = server_response_2["gas"]
            gas_used = server_response_1["gasUsed"]
            gas_price = server_response_2["gasPrice"]/(10**9)
            fee = core_functions.CalculateFee(gas_used, gas_price)
            return {"txh":txh, "status":status, "from_address":from_address, "to_address":to_address, "index_in_the_block":index_in_the_block, "gas_limit":gas_limit, "gas_used":gas_used, "gas_price":gas_price, "bnb_fee":float(fee["bnb_fee"]), "usd_fee":float(fee["usd_fee"])}

    #RESUMO: cria uma nova wallet e retorna o 'address' e 'private key'
    def CreateWallet():
        priv = secrets.token_hex(32)
        private_key = "0x" + priv
        new_wallet_address = core_functions.PVKToAdress(private_key)
        return {"address":new_wallet_address, "private_key":private_key}

    #RESUMO: retorna o 'address' de uma 'pvk'
    def PVKToAdress(wallet_pvk = vars.my_wallet_pvk):
        return str(Account.from_key(wallet_pvk).address)

    #RESUMO: efetua a compra do 'token_address' por 'WBNB' através da DEX pancakeswap
    def BuyToken(token_to, amount, wallet_pvk = vars.my_wallet_pvk, slippage = vars.slippage, gas_limit = 250000, gas_price = 5, seconds_deadline = vars.seconds_deadline):
        seconds_deadline = seconds_deadline*1000
        wallet_address = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(wallet_address)
        checked_token_to = vars.web3.toChecksumAddress(token_to)
        checked_token_from = vars.web3.toChecksumAddress(vars.wbnb_contract)
        validate_amount = core_functions.ValidateAmount(amount, 18)
        if validate_amount["validated"] == False:
            return validate_amount["error"]
        #amountOutMin = vars.pancakeswap_contract.functions.getAmountsOut(int(float(amount)*(10**18)), [checked_token_from, checked_token_to]).call()
        #int(amountOutMin[1]*(1 - slippage))
        amountOutMin = core_functions.AmountOutMin(vars.wbnb_contract, token_to, amount, slippage)
        txh_info = {"from":wallet_address, "value":vars.web3.toWei(amount, "ether"), "gas":gas_limit, "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        trade_txh = vars.pancakeswap_contract.functions.swapExactETHForTokens(amountOutMin, [checked_token_from, checked_token_to], wallet_address, (int(time.time()) + seconds_deadline)).buildTransaction(txh_info)
        signed_txh = vars.web3.eth.account.sign_transaction(trade_txh, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    #RESUMO: efetua a venda do 'token_address' por 'WBNB' através da DEX pancakeswap
    def SellToken(token_from, amount, wallet_pvk = vars.my_wallet_pvk, slippage = vars.slippage, gas_limit = 250000, gas_price = 5, seconds_deadline = vars.seconds_deadline):
        seconds_deadline = seconds_deadline*1000
        wallet_address = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(wallet_address)
        checked_token_to = vars.web3.toChecksumAddress(vars.wbnb_contract)
        checked_token_from = vars.web3.toChecksumAddress(token_from)
        checked_token_contract = core_functions.ReturnContract(vars.wbnb_contract)
        from_decimals = int(checked_token_contract.functions.decimals().call())
        validate_amount = core_functions.ValidateAmount(amount, from_decimals)
        if validate_amount["validated"] == False:
            return validate_amount["error"]
        amountOutMin = vars.pancakeswap_contract.functions.getAmountsOut(int(float(amount)*(10**from_decimals)), [checked_token_from, checked_token_to]).call()
        txh_info = {"from":wallet_address, "value":vars.web3.toWei(0, "ether"), "gas":gas_limit, "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        trade_txh = vars.pancakeswap_contract.functions.swapExactTokensForETH(int(float(amount)*(10**from_decimals)), int(amountOutMin[1]*(1 - slippage)), [checked_token_from, checked_token_to], wallet_address, (int(time.time()) + seconds_deadline)).buildTransaction(txh_info)
        signed_txh = vars.web3.eth.account.sign_transaction(trade_txh, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    #RESUMO: efetua a troca do 'token_from' por 'token_to' através da DEX pancakeswap
    def TradeToken(token_from, amount, token_to = vars.wbnb_contract, wallet_pvk = vars.my_wallet_pvk, slippage = vars.slippage, gas_limit = 250000, gas_price = 5, seconds_deadline = vars.seconds_deadline):
        seconds_deadline = seconds_deadline*1000
        wallet_address = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(wallet_address)
        checked_token_to = vars.web3.toChecksumAddress(token_to)
        checked_token_from = vars.web3.toChecksumAddress(token_from)
        checked_token_from_contract = core_functions.ReturnContract(token_from)
        from_decimals = int(checked_token_from_contract.functions.decimals().call())
        validate_amount = core_functions.ValidateAmount(amount, from_decimals)
        if validate_amount["validated"] == False:
            return validate_amount["error"]
        token_from_price = core_functions.GetTokenPriceByPancakeSwapAPI(token_from)
        amountOutMin = vars.pancakeswap_contract.functions.getAmountsOut(int(float(amount)*(10**from_decimals)), [checked_token_from, checked_token_to]).call()
        txh_info = {"from":wallet_address, "value":vars.web3.toWei(token_from_price["price_bnb"]*amount, "ether"), "gas":gas_limit, "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        trade_txh = vars.pancakeswap_contract.functions.swapExactTokensForTokens(int(float(amount)*(10**from_decimals)), int(amountOutMin[1]*(1 - slippage)), [checked_token_from, checked_token_to], wallet_address, (int(time.time()) + seconds_deadline)).buildTransaction(txh_info)
        signed_txh = vars.web3.eth.account.sign_transaction(trade_txh, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    #RESUMO: realiza allowance (permissão) de um 'token_address' para um 'allowance_address'
    def Approve(token_address, spender_address = vars.pancakeswap_router_address, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price, balance_to_allow = "infinity"):
        wallet_address = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(wallet_address)
        checked_token_address = core_functions.ReturnContract(token_address)
        from_decimals = int(checked_token_address.functions.decimals().call())
        if balance_to_allow == "infinity":
            balance = int(checked_token_address.functions.totalSupply().call())*(10**from_decimals)
        else:
            balance = int((balance_to_allow*(10**from_decimals)) + 1)
        txh_info = {"from":wallet_address, "gas":gas_limit, "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        approve_txh = checked_token_address.functions.approve(spender_address, balance).buildTransaction(txh_info)
        signed_txh = vars.web3.eth.account.sign_transaction(approve_txh, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    #RESUMO: realiza uma transferência de 'wbnb'
    def TransferBNB(to_wallet, amount, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price):
        from_wallet = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(from_wallet)
        validate_amount = core_functions.ValidateAmount(amount, 18)
        if validate_amount["validated"] == False:
            return validate_amount["error"]
        txh_info = {"from":from_wallet, "to":to_wallet, "gas":gas_limit, "value":vars.web3.toWei(amount, "ether"), "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        signed_txh = vars.web3.eth.account.sign_transaction(txh_info, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    #RESUMO: realiza uma transferência de qualquer 'token_address' que não seja 'wbnb'
    def TransferToken(token_address, to_wallet, amount, wallet_pvk = vars.my_wallet_pvk, gas_limit = vars.gas_limit, gas_price = vars.gas_price):
        from_wallet = core_functions.PVKToAdress(wallet_pvk)
        nonce = vars.web3.eth.get_transaction_count(from_wallet)
        checked_token_contract = core_functions.ReturnContract(token_address)
        from_decimals = int(checked_token_contract.functions.decimals().call())
        validate_amount = core_functions.ValidateAmount(amount, from_decimals)
        if validate_amount["validated"] == False:
            return validate_amount["error"]
        txh_info = {"from":from_wallet, "gas":gas_limit, "gasPrice":vars.web3.toWei(str(gas_price), "gwei"), "nonce":nonce}
        transfer_txh = checked_token_contract.functions.transfer(to_wallet, int(amount*(10**from_decimals))).buildTransaction(txh_info)
        signed_txh = vars.web3.eth.account.sign_transaction(transfer_txh, wallet_pvk)
        return {"signed_txh":signed_txh, "estimate_usdfee":0}

    def ReturnContract(token_address, abi = vars.pancakeswap_bep20_functions_abi):
        return vars.web3.eth.contract(address = vars.web3.toChecksumAddress(token_address), abi = abi)

    #RESUMO: submete uma transação
    def SubmitTransaction(signed_txh):
        try:
            raw_transaction = vars.web3.eth.send_raw_transaction(signed_txh.rawTransaction)
            return vars.web3.toHex(raw_transaction)
        except Exception as e:
            return "ERROR: " + str(e)

    #RESUMO: define a taxa da transação em 'usd' calculando o 'gas_price' necessario (precisa ajustes)
    def SetTransactionFee(signed_txh, usd_maxfee = vars.usd_maxfee):
        try:
            estimate_gas = vars.web3.eth.estimate_gas(signed_txh)
            gas_price = (float(core_functions.GetTokenPriceByPancakeSwapAPI(vars.busd_contract)["price_bnb"])*usd_maxfee*0.997)/(estimate_gas/1000000000)
            signed_txh.update({"gasPrice":vars.web3.toWei(str(gas_price), "gwei")})
            estimate_usdfee = core_functions.CalculateFee(estimate_gas, gas_price)["usd_fee"]
            return {"signed_txh":signed_txh, "estimate_usdfee":estimate_usdfee}
        except:
            return "ERROR"

    #RESUMO: cálcula a quantiade do 'token_to' mínimo a ser recebido, segundo slippage (cálculos próprios)
    def AmountOutMin(token_from, token_to, amount, slippage = 0):
        token_from_price = core_functions.GetTokenPriceByPancakeSwapAPI(token_from)
        token_to_price = core_functions.GetTokenPriceByPancakeSwapAPI(token_to)
        token_to_contract = core_functions.ReturnContract(token_to)
        token_to_decimals = int(token_to_contract.functions.decimals().call())
        amountOut = float(token_from_price["price_usd"] * amount)/float(token_to_price["price_usd"])
        amountOut_Uint256 = int((float(amountOut)*(10**token_to_decimals)))
        return amountOut_Uint256*(1 - slippage)

    #RESUMO: cálcula a quantiade do 'token_to' mínimo a ser recebido, segundo slippage (através da pancakeswap)
    def PancakeSwapAmountOutMin(token_from, token_to, amount, slippage = 0):
        token_from_contract = core_functions.ReturnContract(token_from)
        token_from_decimals = int(token_from_contract.functions.decimals().call())
        amountOut_Uint256 = vars.pancakeswap_contract.functions.getAmountsOut(int(float(amount)*(10**token_from_decimals)), [vars.web3.toChecksumAddress(token_from), vars.web3.toChecksumAddress(token_to)]).call()
        return amountOut_Uint256*(1 - slippage)

    #RESUMO: obtenha informações especificadas de qualquer token (mais eficiente chamar esta função quando se deseja pelo menos duas informações)
    def GetTokenInfo(token_address):
        name = ""
        symbol = ""
        decimals = 0
        total_supply = 0
        readble_total_supply = 0
        token_exists = True
        token_contract = core_functions.ReturnContract(token_address)
        try:
            name = str(token_contract.functions.name().call())
            symbol = str(token_contract.functions.symbol().call())
            decimals = int(token_contract.functions.decimals().call())
            total_supply = int(token_contract.functions.totalSupply().call())
            readble_total_supply = int(total_supply/(10**decimals))
        except:
            token_exists = False
        token_info = {"address":token_address, "name":name, "symbol":symbol, "decimals":decimals, "total_supply":total_supply, "readble_total_supply":readble_total_supply, "token_exists":token_exists}
        return token_info

    #RESUMO: retorna a balança de 'token_address' do 'wallet_address'
    def GetTokenBalance(token_address, wallet_address):
        token_contract = core_functions.ReturnContract(token_address)
        decimals = int(token_contract.functions.decimals().call())
        if token_address == vars.wbnb_contract:
            balance = vars.web3.eth.getBalance(wallet_address)
            if balance == 0:
                try:
                    balance = token_contract.functions.balanceOf(wallet_address).call()
                except:
                    pass
        else:
            balance = token_contract.functions.balanceOf(wallet_address).call()
        readble_balance = balance/(10**decimals)
        return {"balance":balance, "readble_balance":readble_balance}

    #RESUMO: retorna o 'allowance' de 'token_address' do 'spender_addres' sobre o 'owner_address'
    def GetTokenAllowance(token_address, owner_address, spender_address):
        token_contract = core_functions.ReturnContract(token_address)
        decimals = int(token_contract.functions.decimals().call())
        allowance = token_contract.functions.allowance(owner_address, spender_address).call()
        readble_allowance_amount = allowance/(10**decimals)
        return {"allowance":allowance, "readble_allowance":readble_allowance_amount}

    #RESUMO: retorna o preço do 'token_address' em 'usd' e 'bnb' de acordo com a pancakeswap (pode estar desatualizado!)
    def GetTokenPriceByPancakeSwapAPI(token_address):
        is_token_listed = True
        usd_price = 0
        bnb_price = 0
        last_price_update = 0
        try:
            html_response = requests.get("https://api.pancakeswap.info/api/v2/tokens/" + token_address).text
            if html_response == '{"error":{"code":404,"message":"Not found"}}':
                raise Exception("token not listed")
            html_dict_list = html_response.replace("{", "").replace("}", "").replace("'", "").replace('"', "").split(",")
            html_dict = {
                "updated_at":int(html_dict_list[0].split(":")[1][:-3]),
                "price_usd":float(html_dict_list[3].split(":")[1]),
                "price_bnb":float(html_dict_list[4].split(":")[1])
            }
            atual_timestamp = int(str(time.time()).split(".")[0])
            last_price_update = atual_timestamp - html_dict["updated_at"]
            usd_price = html_dict["price_usd"]
            bnb_price = html_dict["price_bnb"]
        except:
            is_token_listed = False
        return {"price_usd":usd_price, "price_bnb":bnb_price, "last_price_update_in_seconds":last_price_update, "last_price_update_timestamp":html_dict["updated_at"], "is_token_listed":is_token_listed}

    #RESUMO: retorna o preço do 'token_address' em 'usd' e 'bnb' de acordo com as carteiras de liquidez do token
    #example: liquidity_holders = [{"address":"0xd76026a78a2a9af2f9f57fe6337eed26bfc26aed", "purchase_currency":"BUSD"}, {"address":"0xcdC35B8Ec27E694E42b8c1c25f22629eECCCE80c", "purchase_currency":"WBNB"}]
    #'purchase_currency' reconhecidos são BUSD e WBNB, se a 'purchase_currency' não for nenhuma dessas, digite o 'token_address' da moeda de troca
    def GetTokenPriceByLiquidityHolders(token_address, liquidity_holders):
        qtd_liquidity_holder = len(liquidity_holders)
        total_liquidity = 0
        total_circulating_supply = 0
        for i in range(qtd_liquidity_holder):
            this_purchase_currency_address = ""
            if liquidity_holders[i]["purchase_currency"] == "BUSD":
                this_purchase_currency_address = vars.busd_contract
                purchase_currency_quote = 1
            elif liquidity_holders[i]["purchase_currency"] == "WBNB":
                this_purchase_currency_address = vars.wbnb_contract
                purchase_currency_quote = core_functions.GetTokenPriceByPancakeSwapAPI(vars.wbnb_contract)["price_usd"]
            else:
                this_purchase_currency_address = liquidity_holders[i]["purchase_currency"]
                purchase_currency_quote = core_functions.GetTokenPriceByPancakeSwapAPI(this_purchase_currency_address)["price_usd"]
            this_liquidity = core_functions.GetTokenBalance(this_purchase_currency_address, liquidity_holders[i]["address"])["readble_balance"]*purchase_currency_quote
            this_circulating_supply = core_functions.GetTokenBalance(token_address, liquidity_holders[i]["address"])["readble_balance"]
            total_liquidity += this_liquidity
            total_circulating_supply += this_circulating_supply
        bnb_atual_price = float(core_functions.GetTokenPriceByPancakeSwapAPI(vars.wbnb_contract)["price_usd"])
        usd_price = total_liquidity/total_circulating_supply
        bnb_price = usd_price/bnb_atual_price
        return {"price_usd":usd_price, "price_bnb":bnb_price}

    #RESUMO: cálcula a taxa de uma transação em 'usd' e 'bnb'
    def CalculateFee(gas, gas_price):
        bnb_fee = (int(gas)/1000000000)*float(gas_price)
        usd_fee = float(core_functions.GetTokenPriceByPancakeSwapAPI(vars.wbnb_contract)["price_usd"])*bnb_fee
        return {"bnb_fee":bnb_fee, "usd_fee":usd_fee}

    #RESUMO: conta a quantidade de casas decimais de uma variável do tipo 'decimal.Decimal'
    def HowManyDecimals(decimal_number):
        if str(decimal_number).find(".") != -1:
            from_decimals = len(str(decimal_number).split(".")[1])
        else:
            from_decimals = 0
        return from_decimals

    #RESUMO: verifica se a variável é um 'decimal.Decimal' e verifica se a quantidade de casas decimais da variável ultrapassa a quantidade de casas decimais de um token específico (para evitar transações com quantidade incorreta)
    def ValidateAmount(amount, from_decimals):
        validation = {"validated":True, "error":""}
        if type(amount) != decimal.Decimal:
            validation["validated"] = False
            validation["error"] = "'amount' in not of type 'decimal.Decimal'"
        amount_from_decimals = core_functions.HowManyDecimals(amount)
        if amount_from_decimals > from_decimals:
            validation["validated"] = False
            validation["error"] = "'amount' decimal places exceed 'from_decimals'"
        return validation
