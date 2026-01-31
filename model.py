import pandas as pd
import joblib
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

# Save trained model
joblib.dump(model, "trained_model.pkl")

print("Model saved as trained_model.pkl")
print("Training complete.")
