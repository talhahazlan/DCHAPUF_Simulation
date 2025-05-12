import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam

# Step 1: Load CRPs from CSV
df = pd.read_csv('crps.csv')  

# Convert binary string challenge into numpy array of 0s and 1s
binary_challenges = np.array([[int(bit) for bit in chal] for chal in df['challenge']])
responses = df['response'].values.astype(int)

# Step 2: ML Preprocessing
X_train, X_test, y_train, y_test = train_test_split(binary_challenges, responses, test_size=0.2, random_state=42)
X_train_main, X_val, y_train_main, y_val = train_test_split(X_train, y_train, test_size=0.2, random_state=42)

# Step 3: Logistic Regression Model
lr_model = LogisticRegression(max_iter=1000)
lr_model.fit(X_train_main, y_train_main)
lr_train_acc = lr_model.score(X_train_main, y_train_main)
lr_test_acc = lr_model.score(X_test, y_test)

# Step 4: ANN Model
ann = Sequential([
    Dense(64, activation='relu', input_shape=(64,)),
    Dense(32, activation='relu'),
    Dense(1, activation='sigmoid')
])
ann.compile(optimizer=Adam(learning_rate=0.001), loss='binary_crossentropy', metrics=['accuracy'])

# Train ANN
history = ann.fit(X_train_main, y_train_main, epochs=150, batch_size=64,
                  validation_data=(X_val, y_val), verbose=0)

# Evaluate ANN
ann_train_acc = ann.evaluate(X_train_main, y_train_main, verbose=0)[1]
ann_test_acc = ann.evaluate(X_test, y_test, verbose=0)[1]

# Step 5: Print Accuracy
print(f"ANN Training Accuracy: {ann_train_acc * 100:.2f}%")
print(f"ANN Test Accuracy: {ann_test_acc * 100:.2f}%")
print(f"Logistic Regression Train Accuracy: {lr_train_acc * 100:.2f}%")
print(f"Logistic Regression Test Accuracy: {lr_test_acc * 100:.2f}%")

# Step 6: Plot ANN Training and Validation Accuracy (Real Logs)
epochs_ran = len(history.history['accuracy'])

plt.figure(figsize=(10, 6))
plt.plot(range(1, epochs_ran + 1), history.history['accuracy'], label='Training Accuracy')
plt.plot(range(1, epochs_ran + 1), history.history['val_accuracy'], label='Validation Accuracy')
plt.title('ANN Training vs Validation Accuracy Over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Accuracy')
plt.ylim(0, 1)
plt.xticks(np.arange(0, epochs_ran + 1, step=5))
plt.yticks(np.arange(0.4, 1.05, 0.05))
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig('real_ann_accuracy_plot.png')
plt.show()


# Step 7: Compare Model Accuracies
models = ['Logistic Regression', 'ANN']
train_accuracies = [lr_train_acc * 100, ann_train_acc * 100]
test_accuracies = [lr_test_acc * 100, ann_test_acc * 100]

x = np.arange(len(models))
width = 0.35

plt.figure(figsize=(8, 6))
plt.bar(x - width/2, train_accuracies, width, label='Train Accuracy')
plt.bar(x + width/2, test_accuracies, width, label='Test Accuracy')
plt.ylabel('Accuracy (%)')
plt.title('ML Model Accuracy on Hybrid CT-PUF Dataset')
plt.xticks(x, models)
plt.ylim(0, 100)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig('ml_model_comparison.png')
plt.show()

# Summary Output

print(f"\nTotal CRPs generated: {len(df)}")
print(f"Source file: 'crps.csv'")
print("\n Model Performance:")

print(f" - Logistic Regression Train Accuracy : {lr_train_acc * 100:.2f}%")
print(f" - Logistic Regression Test Accuracy  : {lr_test_acc * 100:.2f}%")
print(f" - ANN Train Accuracy                 : {ann_train_acc * 100:.2f}%")
print(f" - ANN Test Accuracy                  : {ann_test_acc * 100:.2f}%")

# Verdict
if lr_test_acc < 0.60 and ann_test_acc < 0.60:
    verdict = "The PUF is RESISTANT to ML-based attacks!"
else:
    verdict = "The PUF is VULNERABLE to ML-based attacks!"

print("\nVerdict:")
print(verdict)

