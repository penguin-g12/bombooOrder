#!/usr/bin/python3
import sys
import json
import requests
import web3
from web3 import Web3
from random import random
from zero_ex.order_utils import (
    Order,
    asset_data_utils,
    is_valid_signature,
    generate_order_hash_hex,
)


# Default ordee for test
defaultValues = {
    "mId": "ZRX-WETH",
    "action": "buy",
    "maker_amount": "1000000",
    "taker_amount": "1000000",
    "maker_fee": "1000", 
    "taker_fee": "1000",
    "expire_ts": "1616680508"
}

flags = {
    "mId": "-mid",
    "action": "-a",
    "maker_amount": "-ma",
    "taker_amount": "-ta",
    "maker_fee": "-mf", 
    "taker_fee": "-tf",
    "expire_ts": "-et",
}

# Infura
project_id = "b739adb0bb3a48738bf9861e06b3441a"
project_secret = "f31057d1b6fe4d90ba7705f3835e47fe"
http_api = {
    "ropsten": "https://ropsten.infura.io/v3/b739adb0bb3a48738bf9861e06b3441a"
}
wss_api = "wss://rinkeby.infura.io/ws/v3/b739adb0bb3a48738bf9861e06b3441a"

# Ganache
genache = "http://127.0.0.1:8545"

# Eth account 
private_key = "118938281b8c35c9008fabdfb79793b5bdcdee1792b7d0489b1f7d635a3e078e"
account = web3.eth.Account.privateKeyToAccount(private_key)

# Exchange addreses
weth_addr = "0xc778417E063141139Fce010982780140Aa0cD5Ab"
exchange_address = "0xfb2dd2a1366de37f7241c83d47da58fd503e2c64"
xaddr = {
    "main": "0x4f833a24e1f95d70f028921e27040ca56e09ab0b",
    "ropsten": "0xfb2dd2a1366de37f7241c83d47da58fd503e2c64"
}
# BambooRelay
br = {
    "main": "https://rest.bamboorelay.com/main/0x/",
    "ropsten": "https://rest.bamboorelay.com/ropsten/0x/"
}

# Chain ID dictionary
cId = {
    "main": 1,
    "ropsten": 3,
    "genache": 1337
}

# Chosen network
network = "main"

# web3 provider
# w3 = Web3.HTTPProvider(http_api[network])
# print("Connected: " + str(w3.isConnected()))
print("Wallet: " + account.address)

def getTokens():
    r = requests.get(br[network] + 'tokens')
    tokens_info = r.json()
    print(tokens_info)

def getMarkets(id=""):
    mId = ""
    if (id != ""):
        mId = "/" + id
    print(br[network] + 'markets' + mId)
    r = requests.get(br[network] + 'markets' + mId)
    markets_info = r.json()
    return markets_info

def getAccount():
    print(account.address)


def getOrder(id, action, makerAssetAmount, takerAssetAmount, makerFee, takerFee, expirationTimeSeconds):
    token_info = getMarkets(id)
    baseTokenAddress_encoded = "0x" + asset_data_utils.encode_erc20(token_info['baseTokenAddress']).hex()
    quoteTokenAddress_encoded = "0x" + asset_data_utils.encode_erc20(token_info['quoteTokenAddress']).hex()
    return Order(
        makerAddress=account.address,
        takerAddress="0x0000000000000000000000000000000000000000",
        feeRecipientAddress="0xc898fbee1cc94c0ff077faa5449915a506eff384",
        senderAddress="0x0000000000000000000000000000000000000000",
        makerAssetAmount=str(makerAssetAmount),
        takerAssetAmount=str(takerAssetAmount),
        makerFee=str(makerFee),
        takerFee=str(takerFee),
        expirationTimeSeconds=str(expirationTimeSeconds),
        salt=str(round(random() * 100000)),
        makerAssetData=baseTokenAddress_encoded,
        takerAssetData=quoteTokenAddress_encoded,
        makerFeeAssetData=baseTokenAddress_encoded,
        takerFeeAssetData=quoteTokenAddress_encoded,
    )

def orderHash(order, ea):
    return generate_order_hash_hex(order, exchange_address=ea, chain_id=cId[network])


def getArg(arg_type):
    try:
        value = valueByFlag(flags[arg_type])
        return value if value else defaultValues[arg_type]
    except:
        return



def valueByFlag(flag):
    try:
        return sys.argv[sys.argv.index(flag.lower()) + 1]
    except:
        return

def getFeeRecipients():
    r = requests.get("https://sra.bamboorelay.com/0x/v3/fee_recipients")
    rf = r.json()
    return rf
     
def postOrder():
    # api_end_point = br[network] + "orders"
    api_end_point = "https://sra.bamboorelay.com/0x/v3/order"
    print("api_end_point: ", api_end_point)
    print((getArg("mId"), getArg("action"), getArg("maker_amount"), getArg("taker_amount"), getArg("maker_fee"), getArg("taker_fee"), getArg("expire_ts")))
    order = getOrder(getArg("mId"), getArg("action"), getArg("maker_amount"), getArg("taker_amount"), getArg("maker_fee"), getArg("taker_fee"), getArg("expire_ts"))
    oh = orderHash(order, xaddr[network])
    orderResult = {'chainId' : cId[network]}
    orderResult.update(order)
    orderResult['exchangeAddress'] = xaddr[network]
    orderResult['signature'] = account.signHash(oh)['signature'].hex()
    orderJson = json.dumps(orderResult, indent=2)
    print(orderJson)
    r = requests.post(api_end_point, json=orderJson)
    print(r.status_code)
    print(r.text)

def showHelp():
    print_help()
    sys.exit()

def print_help():
    print('Usage [program] [command]')
    print('Commands:')
    print('    getTokens')
    print('    getMarkets')
    print('    postOrder -mId [market-id|default:"' + defaultValues['mId'] + '"] -a [action|"'+defaultValues['action']+'"] -ma [makerAssetAmount|"'+defaultValues['maker_amount']+'"] -ta [takerAssetAmount|"'+defaultValues['taker_amount']+'"] -mf [makerFee|"'+defaultValues['maker_fee']+'"] -tf [takerFee|"'+defaultValues['taker_fee']+'"] -et [expirationTimeSeconds|"'+defaultValues['expire_ts']+'"]')

if __name__ == "__main__":
    if (len(sys.argv)) < 2:
        showHelp()
    command = sys.argv[1].lower()
    if command == "gettokens":
        getTokens()
        sys.exit()
    if command == "getmarkets":
        if (len(sys.argv)) > 2:
            print(getMarkets(sys.argv[2]))
        else:
            print(getMarkets())
        sys.exit()
    if command == "getfee":
        print(getFeeRecipients())
        sys.exit()
    if command == "postorder":
        postOrder()
        sys.exit()
    showHelp()