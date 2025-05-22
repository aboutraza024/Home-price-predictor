import pandas as pd
import re
import nltk
import joblib
from nltk.corpus import stopwords
from sklearn.base import BaseEstimator, TransformerMixin

class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, column_name):
        self.column_name = column_name

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.column_name]
# Download stopwords if not already downloaded
nltk.download('stopwords')

# === Load the saved model ===
model = joblib.load('house_price_model.pkl')  # Path to your saved model

# === Load the new data from CSV ===
data = pd.read_csv('testDATA.csv')  # Replace with your actual file name

# === Clean DESCRIPTION column ===
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\d+', '', text)  # remove digits
    text = re.sub(r'[^\w\s]', '', text)  # remove punctuation
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    filtered = [word for word in tokens if word not in stop_words]
    return " ".join(filtered)

data['DESCRIPTION'] = data['DESCRIPTION'].apply(clean_text)

# === Add binary feature: is_rent ===
data['is_rent'] = data['PURPOSE'].apply(lambda x: 1 if 'rent' in str(x).lower() else 0)

# === Predict prices ===
predictions = model.predict(data)

# === Save results ===
data['Predicted_Price'] = predictions
data.to_csv('predicted_prices.csv', index=False)

# === Optional: print first few rows ===
print(data[['Predicted_Price']].head())
