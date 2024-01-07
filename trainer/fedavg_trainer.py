import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
import numpy as np
import pickle
import os
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

print(alice_on_network)

nonce_holder = AccountNonceHolder(alice_on_network.nonce)

print(alice_on_network.nonce)

sys.exit()

nonce_holder.get_nonce_then_increment()

print(nonce_holder.get_nonce_then_increment())

# Then, sign & broadcast the transaction(s).

call_transaction = sc_factory.create_transaction_for_execute(
    sender=alice,
    contract=contract_address,
    function="set_genesis_address",
    gas_limit=60000000,
    arguments=["Qmdc1jVM494ckaQ6RoHu8qhmuGdGMSxL2r1xF711zKrvQ7"]
)

call_transaction.nonce = 23
call_transaction.signature = signer.sign(transaction_computer.compute_bytes_for_signing(call_transaction))

print("Transaction:", call_transaction.__dict__)
print("Transaction data:", call_transaction.data)


response = network_provider.send_transaction(call_transaction)

print(response)

sys.exit()

# builder = ContractQueryBuilder(
#     contract=contract_address,
#     function="get_genesis_address",
#     call_arguments=[],
#     caller=alice
# )

# query = builder.build()

# network_provider = ApiNetworkProvider("https://devnet-api.multiversx.com")
# response = network_provider.query_contract(query)

# print("Return code:", response.return_code)
# print("Return data:", response.return_data)

# inner_tx = Transaction(
#     sender=alice,
#     contract=contract_address,
#     function="set_genesis_address",
#     gas_limit=60000000,
#     arguments=["Qmdc1jVM494ckaQ6RoHu8qhmuGdGMSxL2r1xF711zKrvQ7"]
# )
# inner_tx.signature = signer.sign(transaction_computer.compute_bytes_for_signing(inner_tx))

# call_transaction = sc_factory.create_transaction_for_execute(inner_tx)

# print("Transaction:", call_transaction.__dict__)
# print("Transaction data:", call_transaction.data)

sys.exit()

def set_genesis_id(genesis_id):
    hex_code = genesis_id.encode('utf-8').hex()
    print(f"Genesis ID: {genesis_id}")
    print(f"The hex conversion: {hex_code}")
    print(sys.path)
    # set_genesis_id_command=['call_contract_set_genesis 0x', hex_code]
    # error = subprocess.run(''.join(set_genesis_id_command), shell=True, capture_output=True, text=True).stderr
    # print(error)
    sys.exit()


def upload_weights_ipfs(weights, directory, filename):
    upload_file = os.path.join(directory, filename)
    with open(upload_file, 'wb') as file:
        pickle.dump(weights, file)
    upload_command = ["ipfs add ", upload_file, " | awk '{print $2}'"]
    upload_file_id = subprocess.run(''.join(upload_command), shell=True, capture_output=True, text=True).stdout[:-1]
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


# Load and preprocess the MNIST dataset
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()
train_images = train_images.reshape((60000, 28, 28, 1)).astype('float32') / 255
test_images = test_images.reshape((10000, 28, 28, 1)).astype('float32') / 255

train_labels = to_categorical(train_labels)
test_labels = to_categorical(test_labels)

# Define the global model
global_model = models.Sequential()
global_model.add(layers.Conv2D(16, (3, 3), activation='relu', input_shape=(28, 28, 1)))
global_model.add(layers.MaxPooling2D((2, 2)))
global_model.add(layers.Flatten())
global_model.add(layers.Dense(10, activation='softmax'))

# Compile the global model
global_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

# Number of clients
num_clients = 10

# Directory to store weights files
weights_dir = 'client_weights'
os.makedirs(weights_dir, exist_ok=True)

global_weights_id = upload_weights_ipfs(global_model.get_weights(), weights_dir, "genesis_weights.pkl")
print(f"Genesis model is uploaded at IPFS ID: {global_weights_id}")

set_genesis_id(global_weights_id)

sys.exit()

# Simulate Federated Learning rounds
for round_num in range(3):
    print(f"\nFederated Learning Round {round_num + 1}")
    
    resulted_upload_files_ids=[]
    
    # Simulate training on each client
    for client_id in range(num_clients):
        print(f"\nTraining on Client {client_id + 1}")
        
        global_weights = download_weights_ipfs(global_weights_id, weights_dir, f'client_{client_id}_round_{round_num}_weights.pkl')
        local_model = tf.keras.models.clone_model(global_model)
        local_model.set_weights(global_weights)
        local_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

        # Simulate training on local data
        local_model.fit(train_images[client_id * 6000 : (client_id + 1) * 6000],
                        train_labels[client_id * 6000 : (client_id + 1) * 6000],
                        epochs=1, batch_size=64, validation_split=0.2)

        
        new_local_id = upload_weights_ipfs(local_model.get_weights(), weights_dir, f'result_client_{client_id}_round_{round_num}_weights.pkl')
        resulted_upload_files_ids.append((client_id, new_local_id))
    
    # Aggregate local updates using FedAvg
    avg_weights = [np.zeros_like(weight) for weight in global_model.get_weights()]

    for (client_id, file_id) in resulted_upload_files_ids:
        # Load local model weights from file
        client_weights = download_weights_ipfs(file_id, weights_dir, f'download_result_client_{client_id}_round_{round_num}_weights.pkl')
        # Aggregate weights
        avg_weights = [avg + local for avg, local in zip(avg_weights, client_weights)]

    # Calculate the average of the weights
    avg_weights = [weight / num_clients for weight in avg_weights]

    # Update the global model with the averaged weights
    global_model.set_weights(avg_weights)
    
    global_weights_id = upload_weights_ipfs(global_model.get_weights(), weights_dir, f'global_weights_after_round_{round_num}')

# Evaluate the final global model on the test set
test_loss, test_acc = global_model.evaluate(test_images, test_labels)
print(f'\nFinal Test Accuracy: {test_acc}')
