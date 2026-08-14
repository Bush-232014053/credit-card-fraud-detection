import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# 1. Load Dataset
data = pd.read_csv("credit_card_fraud_1200_clean.csv")

# 2. Prepare Features and Target Variable
X = data.drop(['Class'], axis=1)

# Add 20% noise to the target variable
np.random.seed(42)
Y_noisy = data["Class"].copy()
noise_idx = np.random.choice(len(Y_noisy), size=int(0.20 * len(Y_noisy)), replace=False)
Y_noisy.iloc[noise_idx] = 1 - Y_noisy.iloc[noise_idx]

# Split data into training and testing sets (80% train, 20% test)
xTrain, xTest, yTrain, yTest = train_test_split(
    X.values, Y_noisy.values, test_size=0.20, random_state=42, stratify=Y_noisy.values
)

# 3. Model Training
rfc = RandomForestClassifier(
    n_estimators=100,
    max_depth=4,
    class_weight='balanced_subsample',
    random_state=42
)
rfc.fit(xTrain, yTrain)

# 4. Save Model
joblib.dump(rfc, "model.pkl")
print("✅ model.pkl file saved successfully!")