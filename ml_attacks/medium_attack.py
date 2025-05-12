import tensorflow as tf
from .base_attack import run_attack

def medium_attack():
    """Medium ANN attack with 3 layers (32,64,64) neurons"""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(32, activation='relu', input_shape=(64,)),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    accuracy = run_attack(
        model=model,
        model_name="Medium",
        train_samples=25000,
        epochs=500
    )
    
    print(f"\nMedium Attack Results:")
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"Resilience: {'HIGH' if accuracy < 0.55 else 'MEDIUM' if accuracy < 0.6 else 'LOW'}")
    return accuracy

if __name__ == "__main__":
    medium_attack()