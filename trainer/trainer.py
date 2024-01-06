import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.datasets import mnist
from tensorflow.keras.utils import to_categorical
import numpy as np

# Load and preprocess the MNIST dataset
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()
train_images = train_images.reshape((60000, 28, 28, 1)).astype('float32') / 255
test_images = test_images.reshape((10000, 28, 28, 1)).astype('float32') / 255

train_labels = to_categorical(train_labels)
test_labels = to_categorical(test_labels)

# Build the simplified neural network model
model = models.Sequential()

# Convolutional layer with 16 filters, each 3x3 in size
model.add(layers.Conv2D(16, (3, 3), activation='relu', input_shape=(28, 28, 1)))
model.add(layers.MaxPooling2D((2, 2)))

# Flatten layer to transform the 2D matrix data to a vector
model.add(layers.Flatten())

# Dense (fully connected) layer with 64 neurons and ReLU activation
model.add(layers.Dense(16, activation='relu'))

# Output layer with 10 neurons (for 10 classes in MNIST) and softmax activation
model.add(layers.Dense(10, activation='softmax'))

# Compile the model
model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

print("Weights before training:")
with open('initial_layer_weights.txt', 'w') as file:
    # Write the weights for each layer
    for layer in model.layers:
        if hasattr(layer, 'get_weights') and layer.get_weights():
            weights = layer.get_weights()[0]
            biases = layer.get_weights()[1] if len(layer.get_weights()) > 1 else None

            file.write(f'{layer.name} - Weights Shape: {weights.shape}\n')
            file.write(np.array_str(weights) + '\n')

            if biases is not None:
                file.write(f'{layer.name} - Biases Shape: {biases.shape}\n')
                file.write(np.array_str(biases) + '\n')

            file.write('\n')

for i in range(5):
    model.fit(train_images, train_labels, epochs=1, batch_size=64, validation_split=0.2)
    with open(f'intermediate_layer_weights_{i}.txt', 'w') as file:
        # Write the weights for each layer
        for layer in model.layers:
            if hasattr(layer, 'get_weights') and layer.get_weights():
                weights = layer.get_weights()[0]
                biases = layer.get_weights()[1] if len(layer.get_weights()) > 1 else None

                file.write(f'{layer.name} - Weights Shape: {weights.shape}\n')
                file.write(np.array_str(weights) + '\n')

                if biases is not None:
                    file.write(f'{layer.name} - Biases Shape: {biases.shape}\n')
                    file.write(np.array_str(biases) + '\n')

                file.write('\n')

with open('results_layer_weights1.txt', 'w') as file:
    # Write the weights for each layer
    for layer in model.layers:
        if hasattr(layer, 'get_weights') and layer.get_weights():
            weights = layer.get_weights()[0]
            biases = layer.get_weights()[1] if len(layer.get_weights()) > 1 else None

            file.write(f'{layer.name} - Weights Shape: {weights.shape}\n')
            file.write(np.array_str(weights) + '\n')

            if biases is not None:
                file.write(f'{layer.name} - Biases Shape: {biases.shape}\n')
                file.write(np.array_str(biases) + '\n')

            file.write('\n')

# Evaluate the model on the test set
test_loss, test_acc = model.evaluate(test_images, test_labels)
print(f'Test accuracy: {test_acc}')
