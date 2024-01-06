import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
import numpy as np
import pickle
import os
import subprocess
import sys

# result = subprocess.run("ipfs add /Users/stefan/ssi-proiect/trainer/fedavg_trainer.py | awk '{print $2}'", shell=True, capture_output=True, text=True)
# print("Output:", result.stdout)
# print("Return Code:", result.returncode)

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

inital_weights_file = os.path.join(weights_dir, f'genesis_weights.pkl')
with open(inital_weights_file, 'wb') as file:
    pickle.dump(global_model.get_weights(), file)

initial_upload_command = ["ipfs add ", inital_weights_file, " | awk '{print $2}'"]
print(''.join(initial_upload_command))

initial_weights_file_id = subprocess.run(''.join(initial_upload_command), shell=True, capture_output=True, text=True).stdout[:-1]

print(f"Genesis model is uploaded at IPFS ID: {initial_weights_file_id}")

# Simulate Federated Learning rounds
for round_num in range(3):
    print(f"\nFederated Learning Round {round_num + 1}")
    
    resulted_upload_files_ids=[]
    
    # Simulate training on each client
    for client_id in range(num_clients):
        print(f"\nTraining on Client {client_id + 1}")

        initial_client_weights_file = os.path.join(weights_dir, f'initial_client_{client_id}_round_{round_num}_weights.pkl')
        with open(initial_client_weights_file, 'w'):
            pass
        
        download_global_command = ["ipfs cat ", initial_weights_file_id, " > ", initial_client_weights_file]
        
        subprocess.run(''.join(download_global_command), shell=True, capture_output=True, text=True)
        
        with open(initial_client_weights_file, 'rb') as file:
            initial_local_weights = pickle.load(file)
        
        # Create a copy of the global model for the client
        local_model = tf.keras.models.clone_model(global_model)
        local_model.set_weights(initial_local_weights)
        local_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

        # Simulate training on local data
        local_model.fit(train_images[client_id * 6000 : (client_id + 1) * 6000],
                        train_labels[client_id * 6000 : (client_id + 1) * 6000],
                        epochs=1, batch_size=64, validation_split=0.2)

        # local_models.append(local_model)
        resulted_weights_file = os.path.join(weights_dir, f'result_client_{client_id}_round_{round_num}_weights.pkl')
        with open(resulted_weights_file, 'wb') as file:
            pickle.dump(local_model.get_weights(), file)

        upload_global_command = ["ipfs add ", resulted_weights_file, " | awk '{print $2}'"]
        resulted_weights_file_id = subprocess.run(''.join(upload_global_command), shell=True, capture_output=True, text=True).stdout[:-1]
        
        resulted_upload_files_ids.append((client_id, resulted_weights_file_id))
        # Get the local model's weights
        # local_weights = local_model.get_weights()

        # # Send local model weights to the server
        # # Simulate communication to a central server (in a real federated learning setup)
        # # In a real setup, you would use a federated learning framework (e.g., TensorFlow Federated)
        # # to handle communication between the server and clients.
        # # Here, we're just directly updating the global model's weights.
        # global_model.set_weights([
        #     (global_weights + local_weights) / 2 for global_weights, local_weights in zip(global_model.get_weights(), local_weights)
        # ])
    
    # Aggregate local updates using FedAvg
    avg_weights = [np.zeros_like(weight) for weight in global_model.get_weights()]

    for (client_id, file_id) in resulted_upload_files_ids:
        # Load local model weights from file
        
        download_result_weights_file = os.path.join(weights_dir, f'download_result_client_{client_id}_round_{round_num}_weights.pkl')
        with open(download_result_weights_file, 'w'):
            pass
        
        download_global_command = ["ipfs cat ", file_id, " > ", download_result_weights_file]
        
        subprocess.run(''.join(download_global_command), shell=True, capture_output=True, text=True)
        
        with open(download_result_weights_file, 'rb') as file:
            local_weights = pickle.load(file)

        # Aggregate weights
        avg_weights = [avg + local for avg, local in zip(avg_weights, local_weights)]

    # Calculate the average of the weights
    avg_weights = [weight / num_clients for weight in avg_weights]

    # Update the global model with the averaged weights
    global_model.set_weights(avg_weights)

# Evaluate the final global model on the test set
test_loss, test_acc = global_model.evaluate(test_images, test_labels)
print(f'\nFinal Test Accuracy: {test_acc}')
