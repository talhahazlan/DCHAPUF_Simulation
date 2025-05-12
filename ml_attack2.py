import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
import matplotlib.pyplot as plt

def load_crps(filename='crps.csv'):
    """Load CRPs from CSV file"""
    df = pd.read_csv(filename)
    X = df.drop('response', axis=1).values.astype(np.float32)
    y = df['response'].values.astype(np.float32)
    return X, y

def build_model(model_type):
    """Construct ANN models based on attack strength"""
    if model_type == 'weak':
        return tf.keras.Sequential([
            tf.keras.layers.Dense(16, activation='relu', input_shape=(64,)),
            tf.keras.layers.Dense(16, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
    elif model_type == 'medium':
        return tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation='relu', input_shape=(64,)),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
    elif model_type == 'strong':
        return tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation='relu', input_shape=(64,)),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(128, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
    elif model_type == 'extreme':
        return tf.keras.Sequential([
            tf.keras.layers.Dense(256, activation='relu', input_shape=(64,)),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])

def train_and_evaluate(model, X_train, y_train, X_test, y_test, epochs, model_type):
    """Train model and evaluate performance"""
    model.compile(optimizer='adam', 
                loss='binary_crossentropy',
                metrics=['accuracy'])
    
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=32,
        validation_split=0.2,
        verbose=0
    )
    
    # Evaluate on test set
    _, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    # Plot training history
    plt.figure(figsize=(10, 5))
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title(f'Learning Curve ({model_type.upper()} Attack)')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.show()
    
    return test_acc

def run_attacks():
    """Run all ML modeling attacks"""
    X, y = load_crps()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    attacks = [
        {'type': 'weak', 'train_samples': 10000, 'epochs': 150},
        # {'type': 'medium', 'train_samples': 25000, 'epochs': 500},
        # {'type': 'strong', 'train_samples': 25000, 'epochs': 1500},
        # {'type': 'extreme', 'train_samples': 100000, 'epochs': 1500}
    ]
    
    results = {}
    
    for attack in attacks:
        model_type = attack['type']
        print(f"\n=== Running {model_type.upper()} Attack ===")
        
        model = build_model(model_type)
        X_subset = X_train[:attack['train_samples']]
        y_subset = y_train[:attack['train_samples']]
        
        test_acc = train_and_evaluate(
            model, X_subset, y_subset,
            X_test, y_test,
            epochs=attack['epochs'],
            model_type=model_type
        )
        
        results[model_type] = test_acc
        print(f"{model_type.upper()} Attack Test Accuracy: {test_acc*100:.2f}%")
    
    # Print final results
    print("\n=== Security Analysis Results ===")
    print("Model Type\t\tAccuracy\tResilience")
    print("-----------------------------------------------")
    for model_type, acc in results.items():
        resilience = "HIGH" if acc < 0.55 else "MEDIUM" if acc < 0.6 else "LOW"
        print(f"{model_type.upper():<16}\t{acc*100:.2f}%\t\t{resilience}")

if __name__ == "__main__":
    run_attacks()