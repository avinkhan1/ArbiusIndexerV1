import os
import json
import requests

from web3 import Web3

from dotenv import load_dotenv


load_dotenv('.env.nova')

API_URL = os.environ.get('NOVA_API_URL')
API_KEY = os.environ.get('NOVA_API_KEY')
RPC_URL = os.environ.get('RPC_URL')
CONTRACT_ADDRESS = os.environ.get('ARBIUS_V1_CA')

abi_endpoint = f"https://api-nova.arbiscan.io/api?module=contract&action=getabi&address={CONTRACT_ADDRESS}&apikey={API_KEY}"
response = requests.get(abi_endpoint)
abi = json.loads(response.json()['result'])
w3 = Web3(Web3.HTTPProvider(RPC_URL))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)


def get_transactions(action, address, start_block, end_block, page, offset, sort):
    params = {
        "module": "account",
        "action": action,
        "address": address,
        "startblock": start_block,
        "endblock": end_block,
        "page": page,
        "offset": offset,
        "sort": sort,
        "apikey": API_KEY
    }
    response = requests.get(API_URL, params=params)
    if response.status_code == 200:
        return response.json()["result"]
    else:
        print("Error fetching transactions:", response.text)
        return []


def get_task_id(input_data):
    # Decode the input data using the contract instance
    try:
        function_obj, function_params = contract.decode_function_input(input_data)
        task_id_bytes = function_params['taskid_']
        task_id_hex = task_id_bytes.hex()
        print("Task ID in hex:", task_id_hex)
        return task_id_hex
    except ValueError as e:
        print(f"Error decoding input data: {e}")
        return None, None