import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
from .base_attack import load_data  

def strong_attack():
    # Load and verify data
    X_train, X_test, y_train, y_test = load_data()
    print(f"Training samples: {len(X_train[:21000])}, Test samples: {len(X_test)}")
    
    # Model architecture - 4 dense layers
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(64, activation='relu', input_shape=(64,)),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(128, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    # Compile with lower learning rate for stability
    model.compile(
        optimizer=tf.keras.optimizers.Adam(0.0005),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    
    # Callbacks for better training
    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor='val_accuracy',
            patience=1500,
            restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            factor=0.5,
            patience=10,
            min_lr=1e-6
        )
    ]
    
    # Train model with more samples and epochs
    history = model.fit(
        X_train[:21000], 
        y_train[:21000],
        epochs=1000,
        batch_size=64,
        validation_split=0.2,
        verbose=1,
        callbacks=callbacks
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
    plt.title('Strong ANN Attack Learning Curve\n(4-Layer Network)', fontsize=14, pad=20)
    plt.xlabel('Epochs', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.xticks(np.arange(0, 1501, 300))
    plt.yticks(np.arange(0.4, 1.1, 0.1))
    plt.ylim(0.4, 1.0)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(loc='lower right', frameon=True)
    
    # Save high-quality image
    plt.savefig('strong_attack_learning_curve.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Get final metrics
    final_train_acc = history.history['accuracy'][-1]
    final_val_acc = history.history['val_accuracy'][-1]
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
    
    # Print comprehensive results
    print("\n=== Strong Attack Results ===")
    print(f"Training Accuracy:   {final_train_acc*100:.2f}%")
    print(f"Validation Accuracy: {final_val_acc*100:.2f}%")
    print(f"Test Accuracy:       {test_acc*100:.2f}%")
    print("="*40)
    
    # Security assessment
    resilience = "HIGH" if test_acc < 0.55 else "MEDIUM" if test_acc < 0.6 else "LOW"
    print(f"Resilience Level:    {resilience}")
    print(f"Secure Threshold:    <55% accuracy (Current: {test_acc*100:.2f}%)")
    
    return test_acc

if __name__ == "__main__":
    strong_attack()