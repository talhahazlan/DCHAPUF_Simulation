import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
from .base_attack import load_data  

def weak_attack():
    # Load and verify data
    X_train, X_test, y_train, y_test = load_data()
    print(f"Training samples: {len(X_train[:10000])}, Test samples: {len(X_test)}")
    
    # Model architecture
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(16, activation='relu', input_shape=(64,)),  # Layer 1: 16 neurons
        tf.keras.layers.Dense(16, activation='relu'),                     # Layer 2: 16 neurons
        tf.keras.layers.Dense(1, activation='sigmoid')                    # Output layer
    ])


    # Compile model
    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.001),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    # Train model
    history = model.fit(
        X_train[:10000], 
        y_train[:10000],
        epochs=500,
        batch_size=32,
        validation_split=0.2,
        verbose=1
    )
    
    # Generate the plot
    plt.figure(figsize=(10, 6))
    
    # Training accuracy (blue)
    plt.plot(history.history['accuracy'], 
             color='#2c7bb6', 
             linewidth=1.5, 
             label='Training Accuracy')
    
    # Validation accuracy (red)
    plt.plot(history.history['val_accuracy'], 
             color='#d7191c', 
             linewidth=1.5, 
             label='Validation Accuracy')
    
    # Horizontal line at 50% (random guessing)
    plt.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Random Guess')
    
    # Styling
    plt.title('Weak ANN Attack Learning Curve', fontsize=14, pad=20)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.xticks(np.arange(0, 501, 100))
    plt.yticks(np.arange(0.4, 1.1, 0.1))
    plt.ylim(0.4, 1.0)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='lower right', frameon=True)
    
    # Save plot
    plt.savefig('weak_attack_learning_curve.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Get final metrics
    final_train_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    # Print results
    print("\n=== Final Metrics ===")
    print(f"Training Accuracy:   {final_train_acc*100:.2f}%")
    print(f"Validation Accuracy: {final_val_acc*100:.2f}%") 
    print(f"Test Accuracy:       {test_acc*100:.2f}%")
    print("="*20)
    print("Note: For a secure PUF, expect accuracies near 50% (±5%)")
    
    return test_acc

if __name__ == "__main__":
    weak_attack()