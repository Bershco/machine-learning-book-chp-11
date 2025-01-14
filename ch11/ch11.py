import sys
from python_environment_check import check_packages
from sklearn.datasets import fetch_openml
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import numpy as np

# ## Implementing a multi-layer perceptron and a multi-layer perceptron with two hidden layers

##########################
### MODEL
##########################

def sigmoid(z):                                        
    return 1. / (1. + np.exp(-z))

def int_to_onehot(y, num_labels):
    ary = np.zeros((y.shape[0], num_labels))
    for i, val in enumerate(y):
        ary[i, val] = 1
    return ary

def softmax(z):
    exp_z = np.exp(z - np.max(z, axis=1, keepdims=True))  # Stability improvement
    return exp_z / np.sum(exp_z, axis=1, keepdims=True)

class NeuralNetMLP:
    def __init__(self, num_features, num_hidden, num_classes, random_seed=123):
        super().__init__()
        self.num_classes = num_classes
        
        # hidden
        rng = np.random.RandomState(random_seed)
        
        self.weight_h = rng.normal(
            loc=0.0, scale=0.1, size=(num_hidden, num_features))
        self.bias_h = np.zeros(num_hidden)
        
        # output
        self.weight_out = rng.normal(
            loc=0.0, scale=0.1, size=(num_classes, num_hidden))
        self.bias_out = np.zeros(num_classes)
        
    def forward(self, x):
        # Hidden layer
        # input dim: [n_examples, n_features] dot [n_hidden, n_features].T
        # output dim: [n_examples, n_hidden]
        z_h = np.dot(x, self.weight_h.T) + self.bias_h
        a_h = sigmoid(z_h)

        # Output layer
        z_out = np.dot(a_h, self.weight_out.T) + self.bias_out
        a_out = softmax(z_out)  # Replaced sigmoid with softmax

        return a_h, a_out

    def backward(self, x, a_h, a_out, y):  
    
        #########################
        ### Output layer weights
        #########################
        
        # onehot encoding
        y_onehot = int_to_onehot(y, self.num_classes)

        # input/output dim: [n_examples, n_classes]
        d_loss__d_a_out = 2.*(a_out - y_onehot) / y.shape[0]

        # input/output dim: [n_examples, n_classes]
        d_a_out__d_z_out = a_out * (1. - a_out) # sigmoid derivative

        # output dim: [n_examples, n_classes]
        delta_out = d_loss__d_a_out * d_a_out__d_z_out # "delta (rule) placeholder"

        # gradient for output weights
        
        # [n_examples, n_hidden]
        d_z_out__dw_out = a_h
        
        # input dim: [n_classes, n_examples] dot [n_examples, n_hidden]
        # output dim: [n_classes, n_hidden]
        d_loss__dw_out = np.dot(delta_out.T, d_z_out__dw_out)
        d_loss__db_out = np.sum(delta_out, axis=0)

        # [n_classes, n_hidden]
        d_z_out__a_h = self.weight_out
        
        # output dim: [n_examples, n_hidden]
        d_loss__a_h = np.dot(delta_out, d_z_out__a_h)
        
        # [n_examples, n_hidden]
        d_a_h__d_z_h = a_h * (1. - a_h) # sigmoid derivative
        
        # [n_examples, n_features]
        d_z_h__d_w_h = x
        
        # output dim: [n_hidden, n_features]
        d_loss__d_w_h = np.dot((d_loss__a_h * d_a_h__d_z_h).T, d_z_h__d_w_h)
        d_loss__d_b_h = np.sum((d_loss__a_h * d_a_h__d_z_h), axis=0)

        return (d_loss__dw_out, d_loss__db_out, 
                d_loss__d_w_h, d_loss__d_b_h)

class NeuralNetMLP2Hidden:
    def __init__(self, num_features, num_hidden1, num_hidden2, num_classes, random_seed=42):
        super().__init__()
        self.num_classes = num_classes

        # hidden 1
        rng = np.random.RandomState(random_seed)

        self.weight_h1 = rng.normal(
            loc=0.0, scale=0.1, size=(num_hidden1, num_features))
        self.bias_h1 = np.zeros(num_hidden1)

        # hidden 2
        self.weight_h2 = rng.normal(
            loc=0.0, scale=0.1, size=(num_hidden2, num_hidden1))
        self.bias_h2 = np.zeros(num_hidden2)

        # output
        self.weight_out = rng.normal(
            loc=0.0, scale=0.1, size=(num_classes, num_hidden2))
        self.bias_out = np.zeros(num_classes)

    def forward(self, x):
        # Hidden 1
        z_h1 = np.dot(x, self.weight_h1.T) + self.bias_h1
        a_h1 = sigmoid(z_h1)

        # Hidden 2
        z_h2 = np.dot(a_h1, self.weight_h2.T) + self.bias_h2
        a_h2 = sigmoid(z_h2)

        # Output layer
        z_out = np.dot(a_h2, self.weight_out.T) + self.bias_out
        a_out = softmax(z_out)  # Replace sigmoid with softmax

        return a_h1, a_h2, a_out

    def backward(self, x, a_h1, a_h2, a_out, y):

        # onehot encoding
        y_onehot = int_to_onehot(y, self.num_classes)

        # Part 1: dLoss/dOutWeights
        d_loss__d_a_out = 2.*(a_out - y_onehot) / y.shape[0]
        d_a_out__d_z_out = a_out * (1. - a_out)
        delta_out = d_loss__d_a_out * d_a_out__d_z_out

        d_z_out__dw_out = a_h2
        d_loss__dw_out = np.dot(delta_out.T, d_z_out__dw_out)
        d_loss__db_out = np.sum(delta_out, axis=0)

        # Part 2: dLoss/dHidden2Weights
        d_z_out__a_h2 = self.weight_out
        d_loss__a_h2 = np.dot(delta_out, d_z_out__a_h2)

        d_a_h2__d_z_h2 = a_h2 * (1. - a_h2)
        d_z_h2__d_w_h2 = a_h1
        d_loss__d_w_h2 = np.dot((d_loss__a_h2 * d_a_h2__d_z_h2).T, d_z_h2__d_w_h2)
        d_loss__d_b_h2 = np.sum((d_loss__a_h2 * d_a_h2__d_z_h2), axis=0)

        # Part 3: dLoss/dHidden1Weights
        d_z_h2__a_h1 = self.weight_h2
        d_loss__a_h1 = np.dot(d_loss__a_h2 * d_a_h2__d_z_h2, d_z_h2__a_h1)

        d_a_h1__d_z_h1 = a_h1 * (1. - a_h1)
        d_z_h1__d_w_h1 = x
        d_loss__d_w_h1 = np.dot((d_loss__a_h1 * d_a_h1__d_z_h1).T, d_z_h1__d_w_h1)
        d_loss__d_b_h1 = np.sum((d_loss__a_h1 * d_a_h1__d_z_h1), axis=0)

        return (d_loss__dw_out, d_loss__db_out,
                d_loss__d_w_h2, d_loss__d_b_h2,
                d_loss__d_w_h1, d_loss__d_b_h1)

# Hyperparameters
num_epochs = 15
print_every_X_epochs = 5
minibatch_size = 100
num_hidden_layer_neurons = 50
learning_rate = 0.5

original_model = NeuralNetMLP(num_features=28 * 28,
                              num_hidden=num_hidden_layer_neurons,
                              num_classes=10)
two_hidden_layers = NeuralNetMLP2Hidden(num_features=28 * 28,
                                        num_hidden1=num_hidden_layer_neurons,
                                        num_hidden2=num_hidden_layer_neurons,
                                        num_classes=10)

# ## Coding the neural network training loop

# Defining data loaders:

def minibatch_generator(X, y, minibatch_size):
    indices = np.arange(X.shape[0])
    np.random.shuffle(indices)
    for start_idx in range(0, indices.shape[0] - minibatch_size + 1, minibatch_size):
        batch_idx = indices[start_idx:start_idx + minibatch_size]
        yield X.iloc[batch_idx], y.iloc[batch_idx]

# Defining a function to compute the loss and accuracy
def probas_processing(probas, correct_pred, num_examples, mse, targets, num_labels):
    predicted_labels = np.argmax(probas, axis=1)
    onehot_targets = int_to_onehot(targets, num_labels=num_labels)
    loss = np.mean((onehot_targets - probas) ** 2)
    correct_pred += (predicted_labels == targets).sum()
    num_examples += targets.shape[0]
    mse += loss
    return correct_pred, num_examples, mse

def compute_mse_and_acc(nnet, X, y, num_labels=10, minibatch_size=100):
    mse, correct_pred, num_examples = 0., 0, 0
    minibatch_gen = minibatch_generator(X, y, minibatch_size)
        
    for i, (features, targets) in enumerate(minibatch_gen):

        _, probas = nnet.forward(features)
        correct_pred, num_examples, mse = probas_processing(probas, correct_pred, num_examples, mse, targets, num_labels)

    mse = mse/(i+1)
    acc = correct_pred/num_examples
    return mse, acc

def compute_mse_and_acc2hidden(nnet, X, y, num_labels=10, minibatch_size=100):
    mse, correct_pred, num_examples = 0., 0, 0
    minibatch_gen = minibatch_generator(X, y, minibatch_size)

    for i, (features, targets) in enumerate(minibatch_gen):

        _, _, probas = nnet.forward(features)
        correct_pred, num_examples, mse = probas_processing(probas, correct_pred, num_examples, mse, targets, num_labels)

    mse = mse/(i+1)
    acc = correct_pred/num_examples
    return mse, acc

from sklearn.metrics import roc_auc_score

def compute_auc(nnet, X, y, num_labels=10, minibatch_size=100):
    probas = []
    targets = []
    minibatch_gen = minibatch_generator(X, y, minibatch_size)

    for features, batch_targets in minibatch_gen:
        _, probas_batch = nnet.forward(features)
        probas.append(probas_batch)
        targets.append(batch_targets)

    # Concatenate probabilities and true labels
    probas = np.vstack(probas)  # Shape: (num_samples, num_labels)
    targets = np.hstack(targets)  # Shape: (num_samples,)

    # Convert targets to one-hot encoding
    onehot_targets = int_to_onehot(targets, num_labels=num_labels)

    # Compute AUC using One-vs-Rest strategy
    auc = roc_auc_score(onehot_targets, probas, multi_class="ovr", average="macro")
    return auc

def compute_auc2hidden(nnet, X, y, num_labels=10, minibatch_size=100):
    probas = []
    targets = []
    minibatch_gen = minibatch_generator(X, y, minibatch_size)

    for features, batch_targets in minibatch_gen:
        _, _, probas_batch = nnet.forward(features)  # Predictions from the model
        probas.append(probas_batch)
        targets.append(batch_targets)

    # Concatenate probabilities and true labels
    probas = np.vstack(probas)  # Shape: (num_samples, num_labels)
    targets = np.hstack(targets)  # Shape: (num_samples,)

    # Convert targets to one-hot encoding
    onehot_targets = int_to_onehot(targets, num_labels=num_labels)

    # Compute AUC using One-vs-Rest strategy
    auc = roc_auc_score(onehot_targets, probas, multi_class="ovr", average="macro")
    return auc

def train(model, X_train, y_train, X_valid, y_valid, num_epochs,
          learning_rate=0.1):
    
    epoch_loss = []
    epoch_train_acc = []
    epoch_valid_acc = []
    
    for e in range(num_epochs):
        _, probas = model.forward(X_test[:5])
        # iterate over minibatches
        minibatch_gen = minibatch_generator(
            X_train, y_train, minibatch_size)

        for i, (X_train_mini, y_train_mini) in enumerate(minibatch_gen):
            #### Compute outputs ####
            a_h, a_out = model.forward(X_train_mini)

            #### Compute gradients ####
            d_loss__d_w_out, d_loss__d_b_out, d_loss__d_w_h, d_loss__d_b_h = model.backward(X_train_mini, a_h, a_out, y_train_mini)

            # prev_weight_out = model.weight_out.copy()
            # prev_weight_h = model.weight_h.copy()

            #### Update weights ####
            model.weight_h -= learning_rate * d_loss__d_w_h
            model.bias_h -= learning_rate * d_loss__d_b_h
            model.weight_out -= learning_rate * d_loss__d_w_out
            model.bias_out -= learning_rate * d_loss__d_b_out

        #### Epoch Logging ####
        train_mse, train_acc = compute_mse_and_acc(model, X_train, y_train)
        valid_mse, valid_acc = compute_mse_and_acc(model, X_valid, y_valid)
        train_acc, valid_acc = train_acc*100, valid_acc*100
        epoch_train_acc.append(train_acc)
        epoch_valid_acc.append(valid_acc)
        epoch_loss.append(train_mse)
        if (e + 1) % print_every_X_epochs == 0:
            print(f'Epoch: {e+1:03d}/{num_epochs:03d} '
                  f'| Train MSE: {train_mse:.2f} '
                  f'| Train Acc: {train_acc:.2f}% '
                  f'| Valid Acc: {valid_acc:.2f}%')

    return epoch_loss, epoch_train_acc, epoch_valid_acc

def train2hidden(model, X_train, y_train, X_valid, y_valid, num_epochs,
                 learning_rate=0.1):

    epoch_loss = []
    epoch_train_acc = []
    epoch_valid_acc = []

    for e in range(num_epochs):
        _, _, probas = model.forward(X_test[:5])

        # iterate over minibatches
        minibatch_gen = minibatch_generator(
            X_train, y_train, minibatch_size)
        for i, (X_train_mini, y_train_mini) in enumerate(minibatch_gen):
            #### Compute outputs ####
            a_h1, a_h2, a_out = model.forward(X_train_mini)

            #### Compute gradients ####
            (d_loss__d_w_out, d_loss__d_b_out,
             d_loss__d_w_h2, d_loss__d_b_h2,
             d_loss__d_w_h1, d_loss__d_b_h1) = model.backward(X_train_mini, a_h1, a_h2, a_out, y_train_mini)

            # prev_weight_out = model.weight_out.copy()
            # prev_weight_h1 = model.weight_h1.copy()
            # prev_weight_h2 = model.weight_h2.copy()

            #### Update weights ####
            model.weight_h1 -= learning_rate * d_loss__d_w_h1
            model.bias_h1 -= learning_rate * d_loss__d_b_h1
            model.weight_h2 -= learning_rate * d_loss__d_w_h2
            model.bias_h2 -= learning_rate * d_loss__d_b_h2
            model.weight_out -= learning_rate * d_loss__d_w_out
            model.bias_out -= learning_rate * d_loss__d_b_out

        #### Epoch Logging ####
        train_mse, train_acc = compute_mse_and_acc2hidden(model, X_train, y_train)
        valid_mse, valid_acc = compute_mse_and_acc2hidden(model, X_valid, y_valid)
        train_acc, valid_acc = train_acc*100, valid_acc*100
        epoch_train_acc.append(train_acc)
        epoch_valid_acc.append(valid_acc)
        epoch_loss.append(train_mse)
        if (e+1) % print_every_X_epochs == 0:
            print(f'Epoch: {e+1:03d}/{num_epochs:03d} '
                  f'| Train MSE: {train_mse:.2f} '
                  f'| Train Acc: {train_acc:.2f}% '
                  f'| Valid Acc: {valid_acc:.2f}%')

    return epoch_loss, epoch_train_acc, epoch_valid_acc

# fetching the MNIST dataset

mnist = fetch_openml('mnist_784', version=1)
X, y = mnist['data'], mnist['target']
y = y.astype(int)
# Normalizing the data

X = X / 255.

# Splitting the data into training and test sets

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42)
# Training the original model

print('Training the original model')
orig_mse, _, _ = train(original_model, X_train, y_train, X_test, y_test, num_epochs=num_epochs, learning_rate=learning_rate)

# Training the model with two hidden layers
print('Training the model with two hidden layers')
new_mse, _, _ = train2hidden(two_hidden_layers, X_train, y_train, X_test, y_test, num_epochs=num_epochs, learning_rate=learning_rate)

# ## Evaluating the models

# Computing the AUC score for the original model

orig_auc = compute_auc(original_model, X_test, y_test)
print(f'Original Model AUC: {orig_auc:.5f}')

# Computing the AUC score for the model with two hidden layers

new_auc = compute_auc2hidden(two_hidden_layers, X_test, y_test)
print(f'Two Hidden Layers Model AUC: {new_auc:.5f}')

# Compare both models to keras

from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
from keras.utils import to_categorical
from sklearn.metrics import roc_auc_score

# One hidden layer model
model = Sequential()
model.add(Dense(100, input_dim=784, activation='sigmoid'))
model.add(Dense(10, activation='softmax'))
model.compile(loss='mse', optimizer=SGD(learning_rate=learning_rate), metrics=['accuracy'])
print('Training Keras model...')
model_history = model.fit(X_train, to_categorical(y_train), epochs=num_epochs, batch_size=minibatch_size, verbose=0)
probas = model.predict(X_test)
print(f'Keras Model AUC: {roc_auc_score(to_categorical(y_test), probas, multi_class="ovr", average="macro"):.5f}')

# Plotting the training and validation loss

plt.plot(range(num_epochs), orig_mse, label='Original Model')
plt.plot(range(num_epochs), new_mse, label='Two Hidden Layers')
plt.plot(range(num_epochs), model_history.history['loss'], label='Keras Model')
plt.ylabel('Mean Squared Error')
plt.xlabel('Epoch')
plt.legend()
plt.title('Training Loss')
plt.text(num_epochs*0.65, 0.05, f'Learning rate: {learning_rate}')
plt.text(num_epochs*0.65, 0.04, f'num_epochs: {num_epochs}')
plt.show()