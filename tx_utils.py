import os
import json
import requests

from web3 import Web3

from dotenv import load_dotenv


load_dotenv('.env.nova')

API_URL = os.environ.get('NOVA_API_URL')
API_KEY = os.environ.get('NOVA_API_KEY')
RPC_URL = os.environ.get('RPC_URL')
CONTRACT_ADDRESS = os.environ.get('ARBIUS_CA')
PROXY_CONTRACT_ADDRESS = os.environ.get('ARBIUS_PROXY_CA')
PRIVATE_KEY = os.environ.get('PRIVATE_KEY')

abi_endpoint = f"https://api-nova.arbiscan.io/api?module=contract&action=getabi&address={CONTRACT_ADDRESS}&apikey={API_KEY}"
response = requests.get(abi_endpoint)
abi = json.loads(response.json()['result'])
w3 = Web3(Web3.HTTPProvider(RPC_URL))
checksum_address = Web3.to_checksum_address(CONTRACT_ADDRESS)
contract = w3.eth.contract(address=checksum_address, abi=abi)


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


def claim_solution(task_id):
    try:
        checksum_address = Web3.to_checksum_address(PROXY_CONTRACT_ADDRESS)
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        account = w3.eth.account.from_key(PRIVATE_KEY)
        contract_function = contract.functions.claimSolution(Web3.to_bytes(hexstr=f"0x{task_id}"))
        nonce = w3.eth.get_transaction_count(account.address)
        transaction = contract_function.build_transaction({
            'chainId': 42170,
            'maxFeePerGas': w3.to_wei(1.55484, 'gwei'),
            'maxPriorityFeePerGas': w3.to_wei(1.5, 'gwei'),
            'gas': 200000,
            'nonce': nonce,
        })
        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
        txn_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        print(f"Transaction hash: {txn_hash.hex()}")
        return True, txn_hash.hex()  # Indicate success and return the transaction hash
    except Exception as e:
        print(f"Error claiming solution for task ID {task_id}: {e}")
        return False, None  # Indicate failure
