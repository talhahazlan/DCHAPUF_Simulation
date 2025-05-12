import tensorflow as tf
from .base_attack import run_attack

def extreme_attack():
    """Extreme ANN attack with 4 deep layers (256,256,256,256) neurons"""
    model = tf.keras.Sequential([
        tf.keras.layers.Dense(256, activation='relu', input_shape=(64,)),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(256, activation='relu'),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    
    accuracy = run_attack(
        model=model,
        model_name="Extreme",
        train_samples=100000,
        epochs=1500
    )
    
    print(f"\nExtreme Attack Results:")
    print(f"Accuracy: {accuracy*100:.2f}%")
    print(f"Resilience: {'HIGH' if accuracy < 0.55 else 'MEDIUM' if accuracy < 0.6 else 'LOW'}")
    return accuracy

if __name__ == "__main__":
    extreme_attack()