import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

def load_emnist():
    # 下载网址：https://www.nist.gov/itl/products-and-services/emnist-dataset
    with open('emnist-balanced-train-images-idx3-ubyte', 'rb') as f:
        X_train = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28)
    with open('emnist-balanced-train-labels-idx1-ubyte', 'rb') as f:
        y_train = np.frombuffer(f.read(), np.uint8, offset=8)

    with open('emnist-balanced-test-images-idx3-ubyte', 'rb') as f:
        X_test = np.frombuffer(f.read(), np.uint8, offset=16).reshape(-1, 28, 28)
    with open('emnist-balanced-test-labels-idx1-ubyte', 'rb') as f:
        y_test = np.frombuffer(f.read(), np.uint8, offset=8)

    return (X_train, y_train), (X_test, y_test)

(X_train, y_train), (X_test, y_test) = load_emnist()
X_train = X_train / 255.0
X_test = X_test / 255.0

X_train = np.transpose(X_train, (0, 2, 1))
X_test = np.transpose(X_test, (0, 2, 1))

X_train = X_train.reshape(-1, 28, 28, 1)
X_test = X_test.reshape(-1, 28, 28, 1)

num_classes = len(np.unique(y_train))
y_train = to_categorical(y_train, num_classes)
y_test = to_categorical(y_test, num_classes)

model = Sequential([
    Conv2D(32, kernel_size=3, activation='relu', input_shape=(28,28,1)),
    MaxPooling2D(pool_size=2),
    Conv2D(64, kernel_size=3, activation='relu'),
    MaxPooling2D(pool_size=2),
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.5),
    Dense(num_classes, activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

model.fit(X_train, y_train, batch_size=128, epochs=10, validation_data=(X_test, y_test))

model.save("cnn_emnist_62class.keras")
print("✅ 模型已保存为 cnn_emnist_62class.keras")