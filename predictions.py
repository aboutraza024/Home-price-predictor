import pandas as pd
import joblib
import nltk
import re
from nltk.corpus import stopwords

from sklearn.base import BaseEstimator, TransformerMixin

class ColumnSelector(BaseEstimator, TransformerMixin):
    def __init__(self, column_name):
        self.column_name = column_name

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[self.column_name]

# Load trained model
model = joblib.load('house_price_model.pkl')

# Define column names (must match training features)
columns = [
    'TYPE', 'DESCRIPTION', 'AREA', 'PRICE', 'PURPOSE',
    'LOCATION', 'BUILD IN YEAR', 'BEDROOMS', 'BATHROOMS', 'PARKING SPACES'
]
# Create DataFrame
new_data = pd.DataFrame([[ "House",
    """
    Double gate house corner 
1 gate =3 cars
2nd gate=3 cars
1 powder 
Double unit house without basement
    """,
    "", "6.75 crore", "For Sell",
    "B-17, Islamabad, Islamabad Capital", "2020", "5", "6", "6"]], columns=columns)

# Download stopwords
nltk.download('stopwords')

# Clean DESCRIPTION
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    tokens = text.split()
    stop_words = set(stopwords.words('english'))
    filtered = [word for word in tokens if word not in stop_words]
    return " ".join(filtered)

new_data['DESCRIPTION'] = new_data['DESCRIPTION'].apply(clean_text)

# Create is_rent feature
new_data['is_rent'] = new_data['PURPOSE'].apply(lambda x: 1 if 'rent' in str(x).lower() else 0)

# Drop 'PRICE' column if it was included in your model's input (this depends on your training)
new_data_for_prediction = new_data.drop(columns=['PRICE'])

# Make prediction
prediction = model.predict(new_data_for_prediction)

# Show and optionally save result
new_data['Predicted_Price'] = prediction
print(new_data[['Predicted_Price']])

