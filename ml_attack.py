import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split

# Load CRPs from CSV
df = pd.read_csv('crps.csv')

# Separate features and labels
X = df.drop('response', axis=1).values.astype(np.float32)
y = df['response'].values.astype(np.float32)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ANN model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(64,)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1, activation='sigmoid')
])
model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])

# Train
model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=0)

# Evaluate
_, accuracy = model.evaluate(X_test, y_test, verbose=0)
print(f"ANN Attack Accuracy: {accuracy * 100:.2f}%")
