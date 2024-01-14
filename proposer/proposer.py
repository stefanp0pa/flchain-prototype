import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
from tensorflow.keras.models import model_from_json
import numpy as np
import pickle
import os
import json
import subprocess
import sys

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

config = TransactionsFactoryConfig(chain_id="D")
transaction_computer = TransactionComputer()
sc_factory = SmartContractTransactionsFactory(config, TokenComputer())
contract_address = Address.from_bech32("erd1qqqqqqqqqqqqqpgq5fqj294099nurngdz9rzgv7du0n6h4vedttshsdl08")
alice = Address.new_from_bech32("erd1hgzhjjw47405npzjh8drx9hx4setln9phu798nhwvtgnz5lmdtts0pze2d")
signer = UserSigner.from_pem_file(Path("/Users/stefan/ssi-proiect/contracts/wallet2.pem"))
network_provider = ApiNetworkProvider("https://devnet-api.multiversx.com")
alice_on_network = network_provider.get_account(alice)

def set_genesis_id(ipfs_file_id):
    # hex_code = ipfs_file_id.encode('utf-8').hex()
    print(f"Genesis ID: {ipfs_file_id}")
    # print(f"The hex conversion: {hex_code}")
    
    nonce_holder = AccountNonceHolder(alice_on_network.nonce)
    print(f'Current nonce: {alice_on_network.nonce}')
    
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=alice,
        contract=contract_address,
        function="set_genesis_address",
        gas_limit=60000000,
        arguments=[ipfs_file_id]
    )
    
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print("Transaction:", call_transaction.__dict__)
    print("Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)


def upload_global_model_ipfs(directory, filename):
    upload_file = os.path.join(directory, filename)
    upload_command = ["ipfs add ", upload_file, " | awk '{print $2}'"]
    upload_file_id = subprocess.run(''.join(upload_command), shell=True, capture_output=True, text=True).stdout[:-1]
    print(f'File {filename} was uploaded to IPFS with ID {upload_file_id}')
    return upload_file_id  


# Define the global model
global_model = models.Sequential()
global_model.add(layers.Conv2D(16, (3, 3), activation='relu', input_shape=(28, 28, 1)))
global_model.add(layers.MaxPooling2D((2, 2)))
global_model.add(layers.Flatten())
global_model.add(layers.Dense(10, activation='softmax'))

# Compile the global model
global_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

directory = '/Users/stefan/ssi-proiect/models/'
filename = 'global_model.keras'
full_filename = directory + filename

global_model.save(full_filename)

file_ipfs_id = upload_global_model_ipfs(directory, filename)
set_genesis_id(file_ipfs_id)