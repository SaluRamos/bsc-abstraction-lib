#system libs
import json
import yaml
#pip libs
from web3 import Web3
from eth_account import Account

class vars:

    #general vars
    bsc = "https://bsc-dataseed.binance.org/"
    web3 = Web3(Web3.HTTPProvider(bsc))
    bscscan_apikey = ""
    pancakeswap_router_address = "0x10ED43C718714eb63d5aA57B78B54704E256024E"
    pancakeswap_main_router_functions_abi_path = open(r"abi/pancakeswap_main_router_functions.json")
    pancakeswap_main_router_functions_abi = json.load(pancakeswap_main_router_functions_abi_path)
    pancakeswap_contract = web3.eth.contract(address = pancakeswap_router_address, abi = pancakeswap_main_router_functions_abi)
    pancakeswap_bep20_functions_abi_path = open(r"abi/bep20_functions.json")
    pancakeswap_bep20_functions_abi = json.load(pancakeswap_bep20_functions_abi_path)

    #todo token contract possui no total 42 caracteres
    wbnb_contract = "0xbb4cdb9cbd36b01bd1cbaebf2de08d9173bc095c"
    busd_contract = "0xe9e7cea3dedca5984780bafc599bd69add087d56"
    burn_address = "0x000000000000000000000000000000000000dEaD"

    #my options
    yaml_options_path = open(r"options.yaml")
    yaml_options = yaml.load(yaml_options_path, Loader = yaml.FullLoader)
    my_wallet_pvk = yaml_options["wallet_pvk"]
    gas_limit = 250000
    gas_price = 5
    usd_maxfee = 1
    slippage = 0.005
    seconds_deadline = 1000