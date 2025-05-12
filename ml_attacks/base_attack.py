import tensorflow as tf
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np

def load_data():
    df = pd.read_csv('./crps.csv')
    print(f"Loaded {len(df)} CRPs")  
    print("Sample challenge:", df.iloc[0, :-1].values)  # Verify first challenge
    print("Sample response:", df.iloc[0, -1])  # Verify first response
    X = df.drop('response', axis=1).values.astype(np.float32)
    y = df['response'].values.astype(np.float32)
    return train_test_split(X, y, test_size=0.2, random_state=42)

def run_attack(model, model_name, train_samples, epochs):
    """Shared attack execution logic"""
    X_train, X_test, y_train, y_test = load_data()
    
    model.compile(optimizer='adam',
                loss='binary_crossentropy',
                metrics=['accuracy'])
    
    history = model.fit(
        X_train[:train_samples], y_train[:train_samples],
        epochs=epochs,
        batch_size=32,
        validation_split=0.2,
        verbose=0
    )
    
    # Evaluation
    _, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    # Plotting
    plt.figure(figsize=(10, 5))
    plt.plot(history.history['accuracy'], label='Train Accuracy')
    plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
    plt.title(f'{model_name} Attack Learning Curve')
    plt.xlabel('Epoch')
    plt.ylabel('Accuracy')
    plt.legend()
    plt.savefig(f'{model_name.lower()}_attack_curve.png')
    plt.close()
    
    return test_acc