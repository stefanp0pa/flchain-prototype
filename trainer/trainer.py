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
import os
import sys
import pika
import pickle
import subprocess
import json
import base64
import random
from dotenv import load_dotenv

load_dotenv()

round = 0
trainer_id = sys.argv[1]

SC_ADDR = "erd1qqqqqqqqqqqqqpgq5fqj294099nurngdz9rzgv7du0n6h4vedttshsdl08"
WALLET_DIR = f"/Users/stefan/ssi-proiect/trainer/trainer{trainer_id}.pem"
TRAINER_ADDR = "erd1fjt6fcxlh89d3jf49kzu7793snlhvptk6fz2kh5g8p8x9jd9lxnskmxxn9"
NETWORK_PROVIDER = "https://devnet-api.multiversx.com"
SC_SIGNUP = "signup"
SC_CURRENT_GLOBAL="get_current_global_version"
SC_UPLOAD_LOCAL="set_local_update"
GAS_LIMIT = 60000000
MODELS_DIR = '/Users/stefan/ssi-proiect/models/'

config = TransactionsFactoryConfig(chain_id="D")
transaction_computer = TransactionComputer()
sc_factory = SmartContractTransactionsFactory(config, TokenComputer())
contract_address = Address.from_bech32(SC_ADDR)
trainer = Address.new_from_bech32(TRAINER_ADDR)
signer = UserSigner.from_pem_file(Path(WALLET_DIR))
network_provider = ApiNetworkProvider(NETWORK_PROVIDER)
proposer_on_network = network_provider.get_account(trainer)

print(f">>>[Trainer {trainer_id}] Loaded dataset")
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()
train_images = train_images.reshape((60000, 28, 28, 1)).astype('float32') / 255
test_images = test_images.reshape((10000, 28, 28, 1)).astype('float32') / 255

train_labels = to_categorical(train_labels)
test_labels = to_categorical(test_labels)
lower_bound_dataset = 0
upper_bound_dataset = 60000

global_model = models.Sequential()
global_model.add(layers.Conv2D(16, (3, 3), activation='relu', input_shape=(28, 28, 1)))
global_model.add(layers.MaxPooling2D((2, 2)))
global_model.add(layers.Flatten())
global_model.add(layers.Dense(10, activation='softmax'))
global_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

def sc_current_global_model():
    builder = ContractQueryBuilder(
        contract=contract_address,
        function=SC_CURRENT_GLOBAL,
        call_arguments=[],
        caller=trainer
    )
    query = builder.build()
    response = network_provider.query_contract(query)
    return base64.b64decode(response.return_data[0]).decode('utf-8')


def sc_upload_local_model(file_id):
    nonce_holder = AccountNonceHolder(proposer_on_network.nonce)
    print(f'>>>[Trainer {trainer_id}] Current nonce: {proposer_on_network.nonce}')
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=trainer,
        contract=contract_address,
        function=SC_UPLOAD_LOCAL,
        gas_limit=GAS_LIMIT,
        arguments=[file_id]
    )
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print(f">>>[Trainer {trainer_id}] Transaction:", call_transaction.__dict__)
    print(f">>>[Trainer {trainer_id}] Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)


def download_weights_ipfs(file_id, directory, filename):
    download_file = os.path.join(directory, filename)
    with open(download_file, 'w'):
        pass

    download_command = ["ipfs cat ", file_id, " > ", download_file]   
    subprocess.run(''.join(download_command), shell=True, capture_output=True, text=True)
    with open(download_file, 'rb') as file:
        weights = pickle.load(file)
    return weights


def upload_weights_ipfs(weights, directory, filename):
    upload_file = os.path.join(directory, filename)
    with open(upload_file, 'wb') as file:
        pickle.dump(weights, file)
    upload_command = ["ipfs add ", upload_file, " | awk '{print $2}'"]
    upload_file_id = subprocess.run(''.join(upload_command), shell=True, capture_output=True, text=True).stdout[:-1]
    print(f'File {filename} was uploaded to IPFS with ID {upload_file_id}')
    return upload_file_id  


def on_training_round_started():
    print(f">>>[Trainer {trainer_id}] Training round started!")
    global_file_id = sc_current_global_model()
    print(f">>>[Trainer {trainer_id}] Downloading global model for round {round} with file ID: {global_file_id}...")
    global_weights = download_weights_ipfs(
        global_file_id, MODELS_DIR, f'pre_training_{trainer_id}_round_{round}_weights.pkl')
    print(f">>>[Trainer {trainer_id}] Downloaded global model for round {round}!")
    local_model = tf.keras.models.clone_model(global_model)
    local_model.set_weights(global_weights)
    local_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    start_subinterval = random.randint(lower_bound_dataset, upper_bound_dataset)
    end_subinterval = random.randint(start_subinterval, upper_bound_dataset)
    local_model.fit(train_images[start_subinterval : end_subinterval],
                    train_labels[start_subinterval : end_subinterval],
                    epochs=1, batch_size=64, validation_split=0.2)
    print(f">>>[Trainer {trainer_id}] Training for round {round} finished!")
    print(f">>>[Trainer {trainer_id}] Uploading local weights for {round} to IPFS...")
    new_local_id = upload_weights_ipfs(local_model.get_weights(), MODELS_DIR, f'post_training_{trainer_id}_round_{round}_weights.pkl')
    print(f">>>[Trainer {trainer_id}] Uploaded local weights to IPFS with ID {new_local_id}!")
    print(f">>>[Trainer {trainer_id}] Uploading local weights to smart contract...")
    sc_upload_local_model(new_local_id)
    print(f">>>[Trainer {trainer_id}] Uploaded local weights to smart contract!")


def on_aggregating_round_started():
    print(f">>>[Trainer {trainer_id}] Aggregating round started!")


def on_session_ended():
    print(f">>>[Trainer {trainer_id}] Session ended!")

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
                if (topic == "training_started_event"):
                    on_training_round_started()
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
        print(f">>>[Trainer {trainer_id}] Successfully connected to RabbitMQ and consuming messages from the queue.")
        channel.start_consuming()
    except Exception as e:
        print(f">>>[Trainer {trainer_id}] Failed to connect to RabbitMQ: {str(e)}")
    finally:
        connection.close()
        sys.exit()
    
    

def sc_signup():
    nonce_holder = AccountNonceHolder(proposer_on_network.nonce)
    print(f'>>>[Trainer {trainer_id}] Current nonce: {proposer_on_network.nonce}')
    call_transaction = sc_factory.create_transaction_for_execute(
        sender=trainer,
        contract=contract_address,
        function=SC_SIGNUP,
        gas_limit=GAS_LIMIT,
        arguments=[1] # TRAINER = 1, AGGREGATOR = 2
    )
    call_transaction.nonce = nonce_holder.get_nonce_then_increment()
    call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

    print(f">>>[Trainer {trainer_id}] Transaction:", call_transaction.__dict__)
    print(f">>>[Trainer {trainer_id}] Transaction data:", call_transaction.data)
    
    response = network_provider.send_transaction(call_transaction)
    print(response)
    

# print(f">>>[Trainer {trainer_id}] Signing up to the current session...")

# # sc_signup()
# print(f">>>[Trainer {trainer_id}] Signed up to the current session!")
print(f">>>[Trainer {trainer_id}] Setting up the events listener...")
setup_events_listener()

