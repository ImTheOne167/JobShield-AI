from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split


# Find the dataset automatically
project_root = Path(__file__).resolve().parent.parent
dataset_path = project_root / "dataset" / "fake_job_postings.csv"

# Load dataset
df = pd.read_csv(dataset_path)

print(f"Dataset loaded: {len(df)} rows")

# Text columns used by the ML model
text_columns = [
    "title",
    "company_profile",
    "description",
    "requirements",
    "benefits",
    "industry",
    "function",
]

# Replace missing values with empty text
for column in text_columns:
    df[column] = df[column].fillna("")

# Combine all useful text into one field
df["combined_text"] = df[text_columns].agg(" ".join, axis=1)

# Target: 0 = legitimate, 1 = fraudulent
X = df["combined_text"]
y = df["fraudulent"]

print("\nClass distribution:")
print(y.value_counts())

# Split into training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y,
)

# Convert text into numerical TF-IDF features
vectorizer = TfidfVectorizer(
    max_features=20000,
    ngram_range=(1, 2),
    min_df=2,
)

X_train_tfidf = vectorizer.fit_transform(X_train)
X_test_tfidf = vectorizer.transform(X_test)

# Train Logistic Regression model
model = LogisticRegression(
    max_iter=1000,
    class_weight="balanced",
)

model.fit(X_train_tfidf, y_train)

# Evaluate the model
predictions = model.predict(X_test_tfidf)

print("\nModel Performance:")
print(classification_report(y_test, predictions))

# Save model and vectorizer
model_path = Path(__file__).resolve().parent / "job_model.pkl"
vectorizer_path = Path(__file__).resolve().parent / "vectorizer.pkl"

joblib.dump(model, model_path)
joblib.dump(vectorizer, vectorizer_path)

print("\nTraining completed successfully!")
print(f"Model saved to: {model_path}")
print(f"Vectorizer saved to: {vectorizer_path}")