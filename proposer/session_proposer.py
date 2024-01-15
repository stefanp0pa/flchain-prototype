import tensorflow as tf
from tensorflow.keras import layers, models
import os
import time
import pickle
import subprocess

from pathlib import Path
from multiversx_sdk_core import TokenComputer
from multiversx_sdk_core.transaction_factories import SmartContractTransactionsFactory
from multiversx_sdk_core.transaction_builders.relayed_v1_builder import RelayedTransactionV1Builder
from multiversx_sdk_core import Transaction, TransactionComputer, Address
from multiversx_sdk_wallet.user_signer import UserSigner
from multiversx_sdk_core.transaction_factories import TransactionsFactoryConfig
from multiversx_sdk_core import ContractQueryBuilder
from multiversx_sdk_network_providers import ApiNetworkProvider
from multiversx_sdk_core import AccountNonceHolder

SC_ADDR = "erd1qqqqqqqqqqqqqpgq5fqj294099nurngdz9rzgv7du0n6h4vedttshsdl08"
WALLET_DIR = "/Users/stefan/ssi-proiect/proposer/proposer.pem"
PROPOSER_ADDR = "erd1rrpflqfed0dvc0yptw4lurxf2cjnfvvlavlg26rq7cvcp36tyfvsu3hr8d"
NETWORK_PROVIDER = "https://devnet-api.multiversx.com"
SC_START_SESSION = "start_session"
SC_SET_ACTIVE_ROUND="set_active_round"
GAS_LIMIT = 60000000
MODELS_DIR = '/Users/stefan/ssi-proiect/models/'
GLOBAL_MODEL_FILE = 'global_model.pkl'
FULL_FILENAME = MODELS_DIR + GLOBAL_MODEL_FILE
NEXT_ROUND = 2

config = TransactionsFactoryConfig(chain_id="D")
transaction_computer = TransactionComputer()
sc_factory = SmartContractTransactionsFactory(config, TokenComputer())
contract_address = Address.from_bech32(SC_ADDR)
proposer = Address.new_from_bech32(PROPOSER_ADDR)
signer = UserSigner.from_pem_file(Path(WALLET_DIR))
network_provider = ApiNetworkProvider(NETWORK_PROVIDER)


def sc_start_next_round():
    nonce_holder = AccountNonceHolder(network_provider.get_account(proposer).nonce)
    print(f'>>>[Proposer] Current nonce: {network_provider.get_account(proposer).nonce}')
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=proposer,
        contract=contract_address,
        function=SC_SET_ACTIVE_ROUND,
        gas_limit=GAS_LIMIT,
        arguments=[NEXT_ROUND]
    )
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print(">>>[Proposer] Transaction:", call_transaction.__dict__)
    print(">>>[Proposer] Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)


def sc_start_session(file_id):
    nonce_holder = AccountNonceHolder(network_provider.get_account(proposer).nonce)
    print(f'>>>[Proposer] Current nonce: {network_provider.get_account(proposer).nonce}')
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=proposer,
        contract=contract_address,
        function=SC_START_SESSION,
        gas_limit=GAS_LIMIT,
        arguments=[file_id, 200, 10, 10]
    )
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print(">>>[Proposer] Transaction:", call_transaction.__dict__)
    print(">>>[Proposer] Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)


def upload_global_model_ipfs(weights, directory, filename):
    upload_file = os.path.join(directory, filename)
    with open(upload_file, 'wb') as file:
        pickle.dump(weights, file)
    upload_command = ["ipfs add ", upload_file, " | awk '{print $2}'"]
    upload_file_id = subprocess.run(''.join(upload_command), shell=True, capture_output=True, text=True).stdout[:-1]
    print(f'>>>[Proposer] {filename} was uploaded to IPFS with ID {upload_file_id}')
    return upload_file_id



print(">>>[Proposer] Initializing global model...")

global_model = models.Sequential()
global_model.add(layers.Conv2D(16, (3, 3), activation='relu', input_shape=(28, 28, 1)))
global_model.add(layers.MaxPooling2D((2, 2)))
global_model.add(layers.Flatten())
global_model.add(layers.Dense(10, activation='softmax'))

global_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

print(f">>>[Proposer] Global model initialized and saved to {FULL_FILENAME}")
file_id = upload_global_model_ipfs(global_model.get_weights(), MODELS_DIR, GLOBAL_MODEL_FILE)
print(f">>>[Proposer] Global model uploaded to IPFS")

# start session
sc_start_session(file_id)

print(">>>[Proposer] Session started successfully!")

time.sleep(5)
sc_start_next_round()