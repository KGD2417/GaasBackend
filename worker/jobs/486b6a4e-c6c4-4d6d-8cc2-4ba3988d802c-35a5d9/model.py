import pandas as pd
import joblib
import base64
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error

print("Loading dataset...")

df = pd.read_csv("dataset.csv")

X = df[["size", "bedrooms", "age"]]
y = df["price"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print("Training model...")

model = LinearRegression()
model.fit(X_train, y_train)

predictions = model.predict(X_test)
mse = mean_squared_error(y_test, predictions)

print("Model coefficients:", model.coef_)
print("Mean Squared Error:", mse)

# =====================================
# 🔥 SAVE TRAINED MODEL
# =====================================
model_path = "trained_model.pkl"
joblib.dump(model, model_path)

print("Model saved as trained_model.pkl")

# =====================================
# 🔥 ENCODE MODEL FOR GAAS RETURN
# =====================================
with open(model_path, "rb") as f:
    model_bytes = f.read()

model_base64 = base64.b64encode(model_bytes).decode()

print("MODEL_BASE64_START")
print(model_base64)
print("MODEL_BASE64_END")

print("Training complete.")