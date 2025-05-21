import tensorflow as tf
import matplotlib.pyplot as plt
import numpy as np
from base_attack import load_data


def logistic_regression_attack():
    # Load and verify data
    X_train, X_test, y_train, y_test = load_data()
    print(f"Training samples: {len(X_train)}, Test samples: {len(X_test)}")
   
    # Logistic regression model (single layer)
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(1, activation='sigmoid', input_shape=(64,))
    ])
   
    # Compile with conservative learning rate
    model.compile(
        optimizer=tf.keras.optimizers.SGD(learning_rate=0.01),
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
   
    # Training configuration
    history = model.fit(
        X_train,
        y_train,
        epochs=200,
        batch_size=256,
        validation_split=0.2,
        verbose=1,
        callbacks=[
            tf.keras.callbacks.EarlyStopping(
                monitor='val_accuracy',
                patience=20,
                restore_best_weights=True
            )
        ]
    )
   
    # Generate plot
    plt.figure(figsize=(10, 6))
    plt.plot(history.history['accuracy'], color='blue', label='Training Accuracy')
    plt.plot(history.history['val_accuracy'], color='red', label='Validation Accuracy')
    plt.axhline(y=0.5, color='gray', linestyle='--', label='Random Guess')
   
    plt.title('Logistic Regression Attack Performance')
    plt.xlabel('Epochs')
    plt.ylabel('Accuracy')
    plt.ylim(0.4, 1.0)
    plt.legend()
    plt.grid(True)
    plt.savefig('logistic_regression_attack.png', dpi=300)
    plt.close()
   
    # Evaluation
    test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
   
    print("\n=== Logistic Regression Results ===")
    print(f"Final Training Accuracy: {history.history['accuracy'][-1]*100:.2f}%")
    print(f"Final Validation Accuracy: {history.history['val_accuracy'][-1]*100:.2f}%")
    print(f"Test Accuracy: {test_acc*100:.2f}%")
   
    # Security assessment
    security_status = "Secure" if test_acc < 0.55 else "Vulnerable"
    print(f"\nSecurity Status: {security_status} (Threshold: <55% accuracy)")
   
    return test_acc


if __name__ == "__main__":
    logistic_regression_attack()


