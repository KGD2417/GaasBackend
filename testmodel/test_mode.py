import pandas as pd
import joblib
from sklearn.metrics import mean_squared_error

print("Loading trained model...")
model = joblib.load("trained_model.pkl")

print("Loading dataset...")
df = pd.read_csv("dataset.csv")

X = df[["size", "bedrooms", "age"]]
y = df["price"]

print("Making predictions...")
predictions = model.predict(X)

# Show predictions
for i in range(len(predictions)):
    print(
        f"Input: {X.iloc[i].values} | "
        f"Actual Price: {y.iloc[i]} | "
        f"Predicted Price: {round(predictions[i], 2)}"
    )

# Calculate error
mse = mean_squared_error(y, predictions)
print("\nModel MSE:", mse)

# ----------------------------
# Custom Manual Test
# ----------------------------
print("\nTest custom house:")
size = float(input("Enter size: "))
bedrooms = float(input("Enter bedrooms: "))
age = float(input("Enter age: "))

custom_pred = model.predict([[size, bedrooms, age]])
print("Predicted Price:", round(custom_pred[0], 2))
