import pandas as pd
import numpy as np
import pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

print("1. Generating Large Synthetic Dataset (50,000 records)...")
np.random.seed(42)
n_samples = 50000

# Generate normal random distributions for features
voter_age = np.random.randint(18, 95, n_samples)
vote_hour = np.random.randint(0, 24, n_samples)
time_taken_seconds = np.random.randint(1, 300, n_samples)
# 0: Mobile, 1: Desktop, 2: Tablet, 3: Server/Proxy
device_type = np.random.choice([0, 1, 2, 3], n_samples, p=[0.5, 0.35, 0.1, 0.05])
# 70% of people have 0 fails. Fraudsters have many.
failed_login_attempts = np.random.choice([0, 1, 2, 3, 4, 5], n_samples, p=[0.7, 0.15, 0.05, 0.05, 0.03, 0.02])

# Build the DataFrame
df = pd.DataFrame({
    'voter_age': voter_age,
    'vote_hour': vote_hour,
    'time_taken_seconds': time_taken_seconds,
    'device_type': device_type,
    'failed_login_attempts': failed_login_attempts
})

print("2. Applying Fraud Logic Rules...")
# We establish baseline rules for what constitutes a "Fraudulent" vote.
# The ML model will learn these patterns and their complex interactions.
is_fraud = []
for index, row in df.iterrows():
    fraud_score = 0
    
    # Bots vote instantly
    if row['time_taken_seconds'] < 5:
        fraud_score += 3
        
    # Server/Proxy activity in the middle of the night
    if row['device_type'] == 3 and (row['vote_hour'] >= 1 and row['vote_hour'] <= 4):
        fraud_score += 3
        
    # Brute force login attempts
    if row['failed_login_attempts'] >= 3:
        fraud_score += 2
        
    # Random chance of human error/anomaly to make the dataset realistic (noise)
    if np.random.rand() < 0.02:
        fraud_score += 2
        
    # If the score is high enough, label it as fraud (1), else normal (0)
    is_fraud.append(1 if fraud_score >= 3 else 0)

df['is_fraud'] = is_fraud

# Save the dataset so you can view it in Excel/VS Code
csv_filename = "voting_fraud_dataset_large.csv"
df.to_csv(csv_filename, index=False)
print(f"-> Dataset saved successfully as '{csv_filename}'.\n")

print("3. Training the Machine Learning Engine...")
# Separate Features (X) and Target (y)
X = df[['voter_age', 'vote_hour', 'time_taken_seconds', 'device_type', 'failed_login_attempts']]
y = df['is_fraud']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a robust Random Forest model
model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
model.fit(X_train, y_train)

print("4. Evaluating Model Performance...")
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"-> Accuracy: {accuracy * 100:.2f}%")
print("\nClassification Report:\n", classification_report(y_test, predictions))

print("5. Exporting Model to Flask...")
model_filename = 'model.pkl'
with open(model_filename, 'wb') as file:
    pickle.dump(model, file)

print(f"-> Model saved as '{model_filename}'. Your system is ready!")