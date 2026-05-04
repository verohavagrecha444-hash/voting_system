from sklearn.tree import plot_tree
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle

# =========================
# STEP 1: Load Dataset
# =========================
data = pd.read_csv("voting_fraud_dataset_large.csv")

print("\nDataset Preview:")
print(data.head())

# =========================
# STEP 2: Separate Features & Target
# =========================
X = data.drop("is_fraud", axis=1)
y = data["is_fraud"]

# =========================
# STEP 3: Convert Categorical to Numeric
# =========================
X = pd.get_dummies(X)

# 🔥 SAVE FEATURE NAMES (VERY IMPORTANT)
feature_names = X.columns

# =========================
# STEP 4: Split Data
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# =========================
# STEP 5: Train Model (IMPROVED)
# =========================
model = DecisionTreeClassifier(
    max_depth=5,          # prevent overfitting
    min_samples_split=10,
    random_state=42
)

model.fit(X_train, y_train)

# =========================
# STEP 6: Prediction
# =========================
y_pred = model.predict(X_test)

# =========================
# STEP 7: Evaluation
# =========================
accuracy = accuracy_score(y_test, y_pred)
cm = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred)

print("\nAccuracy:", accuracy)
print("\nConfusion Matrix:\n", cm)
print("\nClassification Report:\n", report)

# =========================
# STEP 8: Save Confusion Matrix
# =========================
plt.figure(figsize=(5,4))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
plt.title("Confusion Matrix")
plt.xlabel("Predicted")
plt.ylabel("Actual")

plt.savefig("confusion_matrix.png")
plt.close()

print("Confusion matrix saved")

# =========================
# STEP 9: Save Decision Tree
# =========================
plt.figure(figsize=(20,10))
plot_tree(model, feature_names=feature_names, class_names=["Valid","Fraud"], filled=True, max_depth=3)
plt.title("Decision Tree Visualization")

plt.savefig("decision_tree.png")
plt.close()

print("Decision tree saved")

# =========================
# STEP 10: Save Model + FEATURES
# =========================
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

# 🔥 SAVE FEATURES SEPARATELY
with open("features.pkl", "wb") as f:
    pickle.dump(feature_names, f)

print("Model and features saved successfully!")