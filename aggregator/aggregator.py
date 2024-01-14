from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical

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
import tensorflow as tf
import numpy as np
import os
import sys
import pika
import pickle
import subprocess
import json
import base64
import random
import re

from dotenv import load_dotenv

load_dotenv()

SC_ADDR = "erd1qqqqqqqqqqqqqpgq5fqj294099nurngdz9rzgv7du0n6h4vedttshsdl08"
WALLET_DIR = "/Users/stefan/ssi-proiect/aggregator/aggregator.pem"
TRAINER_ADDR = "erd1shvhh4rukxth6vf4fcpa9p8t54y7jxqdtfg8x0zs9hhesqzdm7ysa9g6t7"
NETWORK_PROVIDER = "https://devnet-api.multiversx.com"
SC_DOWNLOAD_LOCAL = "get_local_updates"
SC_NEW_GLOBAL = "set_global_version"
SC_CURRENT_GLOBAL="get_current_global_version"
GAS_LIMIT = 60000000
MODELS_DIR = '/Users/stefan/ssi-proiect/models/'

config = TransactionsFactoryConfig(chain_id="D")
transaction_computer = TransactionComputer()
sc_factory = SmartContractTransactionsFactory(config, TokenComputer())
contract_address = Address.from_bech32(SC_ADDR)
aggregator = Address.new_from_bech32(TRAINER_ADDR)
signer = UserSigner.from_pem_file(Path(WALLET_DIR))
network_provider = ApiNetworkProvider(NETWORK_PROVIDER)
proposer_on_network = network_provider.get_account(aggregator)

def upload_weights_ipfs(weights, directory, filename):
    upload_file = os.path.join(directory, filename)
    with open(upload_file, 'wb') as file:
        pickle.dump(weights, file)
    upload_command = ["ipfs add ", upload_file, " | awk '{print $2}'"]
    upload_file_id = subprocess.run(''.join(upload_command), shell=True, capture_output=True, text=True).stdout[:-1]
    print(f'File {filename} was uploaded to IPFS with ID {upload_file_id}')
    return upload_file_id   

def download_weights_ipfs(file_id, directory, filename):
    download_file = os.path.join(directory, filename)
    with open(download_file, 'w'):
        pass

    download_command = ["ipfs cat ", file_id, " > ", download_file]   
    subprocess.run(''.join(download_command), shell=True, capture_output=True, text=True)
    with open(download_file, 'rb') as file:
        weights = pickle.load(file)
    return weights

def sc_set_global_model(file_id):
    nonce_holder = AccountNonceHolder(proposer_on_network.nonce)
    print(f'>>>[Proposer] Current nonce: {proposer_on_network.nonce}')
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=aggregator,
        contract=contract_address,
        function=SC_NEW_GLOBAL,
        gas_limit=GAS_LIMIT,
        arguments=[file_id]
    )
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print(">>>[Proposer] Transaction:", call_transaction.__dict__)
    print(">>>[Proposer] Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)

def sc_get_local_updates():
    builder = ContractQueryBuilder(
        contract=contract_address,
        function=SC_DOWNLOAD_LOCAL,
        call_arguments=[],
        caller=aggregator
    )
    query = builder.build()
    response = network_provider.query_contract(query)
    result = base64.b64decode(response.return_data[0]).decode('utf-8').rstrip('\x00')
    print(result)
    parsed = result.split('.')
    parsed = map(lambda x: x.rstrip('\x00'), parsed)
    parsed = list(parsed)
    return parsed[1:]

def sc_current_global_model():
    builder = ContractQueryBuilder(
        contract=contract_address,
        function=SC_CURRENT_GLOBAL,
        call_arguments=[],
        caller=aggregator
    )
    query = builder.build()
    response = network_provider.query_contract(query)
    return base64.b64decode(response.return_data[0]).decode('utf-8').rstrip('\x00')


def on_aggregating_round_started():
    print(f">>>[Aggregator] Aggregating round started!")
    curr_global_id = sc_current_global_model()
    print(f">>>[Aggregator] Current global model ID: {curr_global_id}")
    global_weights = download_weights_ipfs(curr_global_id, MODELS_DIR, "curr_global_model.pkl")
    avg_weights = [np.zeros_like(weight) for weight in global_weights]
    print(f">>>[Aggregator] Downloading local updates...")
    local_updates_ids = sc_get_local_updates()
    print(f">>>[Aggregator] Local updates IDs: {local_updates_ids}")
    for file_id in local_updates_ids:
        print("aa")
        client_weights = download_weights_ipfs(file_id, MODELS_DIR, f'download_result_client_weights.pkl')
        avg_weights = [avg + local for avg, local in zip(avg_weights, client_weights)]

    # Calculate the average of the weights
    avg_weights = [weight / len(local_updates_ids) for weight in avg_weights]
    new_global_id = upload_weights_ipfs(avg_weights, MODELS_DIR, f'new_global_weights.pkl')
    sc_set_global_model(new_global_id)
    

def process_blockchain_event(channel, method, properties, body):
    events = json.loads(body.decode('utf-8'))
    just_events = events.get('events', [])
    possible_events = [
        "start_session",
        "end_session",
        "signup",
        "set_active_round",
        "signup_started_event",
        "training_started_event",
        "aggregation_started_event"]

    for event in just_events:
        if event['identifier'] in possible_events:
            print(event['identifier'])
            identifier = event['identifier']
            topic = base64.b64decode(event['topics'][0]).decode('utf-8')
            print(f"Received event {identifier}-{topic}")
            if (identifier == "set_active_round"):
                if (topic == "aggregation_started_event"):
                    on_aggregating_round_started()
            else:
                print(f"Do nothing for {identifier}-{topic}")


def setup_events_listener():
    host = os.getenv("BEACONX_HOST")
    port = os.getenv("BEACONX_PORT")
    username = os.getenv("BEACONX_USER")
    password = os.getenv("BEACONX_PASSWORD")
    virtual_host = os.getenv("BEACONX_VIRTUAL_HOST")
    queue_name = os.getenv("BEACONX_QUEUE")
    credentials = pika.PlainCredentials(username, password)
    parameters = pika.ConnectionParameters(host=host, port=port, virtual_host=virtual_host, credentials=credentials)
    connection = pika.BlockingConnection(parameters)
    try:
        channel = connection.channel()
        channel.basic_consume(queue=queue_name, on_message_callback=process_blockchain_event, auto_ack=True)
        print(f">>>[Aggregator] Successfully connected to RabbitMQ and consuming messages from the queue.")
        channel.start_consuming()
    except Exception as e:
        print(f">>>[Aggregator] Failed to connect to RabbitMQ: {str(e)}")
    finally:
        connection.close()
        sys.exit()
    
print(f">>>[Aggregator] Setting up the events listener...")
setup_events_listener()