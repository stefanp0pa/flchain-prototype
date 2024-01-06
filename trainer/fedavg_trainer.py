import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
import numpy as np
import pickle
import os

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
num_clients = 20

# Directory to store weights files
weights_dir = 'client_weights'
os.makedirs(weights_dir, exist_ok=True)

# Simulate Federated Learning rounds
for round_num in range(10):
    print(f"\nFederated Learning Round {round_num + 1}")
    
    local_models = []
    # Simulate training on each client
    for client_id in range(num_clients):
        print(f"\nTraining on Client {client_id + 1}")

        # Create a copy of the global model for the client
        local_model = tf.keras.models.clone_model(global_model)
        local_model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

        # Simulate training on local data
        local_model.fit(train_images[client_id * 3000 : (client_id + 1) * 3000],
                        train_labels[client_id * 3000 : (client_id + 1) * 3000],
                        epochs=1, batch_size=64, validation_split=0.2)

        # local_models.append(local_model)
        weights_file = os.path.join(weights_dir, f'client_{client_id}_weights.pkl')
        with open(weights_file, 'wb') as file:
            pickle.dump(local_model.get_weights(), file)

        
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

    # for local_model in local_models:
    #     local_weights = local_model.get_weights()

    #     for i in range(len(avg_weights)):
    #         avg_weights[i] += local_weights[i]
    for client_id in range(num_clients):
        # Load local model weights from file
        weights_file = os.path.join(weights_dir, f'client_{client_id}_weights.pkl')
        with open(weights_file, 'rb') as file:
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
