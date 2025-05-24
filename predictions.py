import joblib
import pandas as pd

# Load model
model, feature_names = joblib.load("home_price_model.pkl")

def predict_price(user_input: dict):
    input_df = pd.DataFrame([user_input])
    return model.predict(input_df)[0]

# Example
sample = {
    "TYPE": "House",
    "AREA": 16000,
    "PURPOSE": "for sale",
    "LOCATION": "F-8, Islamabad, Islamabad Capital",
    "BUILD IN YEAR": 2020,
    "BEDROOMS": 5,
    "BATHROOMS": 6,
    "PARKING SPACES": 3
}

print(f"Predicted Price: Rs {predict_price(sample):,.0f}")
