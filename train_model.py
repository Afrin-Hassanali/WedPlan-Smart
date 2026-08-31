import pandas as pd
import joblib

from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score


# =====================================================
# 1. FIND PROJECT DIRECTORIES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset.xlsx"
)

MODEL_DIR = BASE_DIR / "model"

MODEL_DIR.mkdir(
    exist_ok=True
)

MODEL_PATH = (
    MODEL_DIR
    / "wedplan_recommendation_model.pkl"
)


# =====================================================
# 2. CHECK DATASET
# =====================================================

if not DATASET_PATH.exists():

    raise FileNotFoundError(
        "\nDataset not found!\n"
        f"Expected location:\n{DATASET_PATH}\n"
    )


# =====================================================
# 3. LOAD DATASET
# =====================================================

data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


print("====================================")
print("WEDPLAN SMART MODEL TRAINING")
print("====================================")

print()
print("Dataset loaded successfully!")

print("Dataset path:")
print(DATASET_PATH)

print()
print("Total records:", len(data))


# =====================================================
# 4. BASIC DATA VALIDATION
# =====================================================

required_columns = [
    "category",
    "location",
    "price_lkr",
    "guest_capacity",
    "rating",
    "review_count",
    "wedding_style",
    "popularity_score",
    "available",
    "suitability_score"
]

missing_columns = [
    column
    for column in required_columns
    if column not in data.columns
]

if missing_columns:

    raise ValueError(
        "\nMissing required columns:\n"
        + "\n".join(missing_columns)
    )


# =====================================================
# 5. DATASET INFORMATION
# =====================================================

print()
print("====================================")
print("DATASET INFORMATION")
print("====================================")

print()
print("Wedding styles:")

print(
    data["wedding_style"]
    .value_counts()
)

print()
print("Service categories:")

print(
    data["category"]
    .value_counts()
)

print()
print("Locations:")

print(
    data["location"].nunique(),
    "unique locations"
)


# =====================================================
# 6. SELECT FEATURES
# =====================================================

features = [
    "category",
    "location",
    "price_lkr",
    "guest_capacity",
    "rating",
    "review_count",
    "wedding_style",
    "popularity_score",
    "available"
]

target = "suitability_score"


X = data[features].copy()

y = data[target].copy()


# =====================================================
# 7. DEFINE FEATURE TYPES
# =====================================================

categorical_features = [
    "category",
    "location",
    "wedding_style",
    "available"
]

numerical_features = [
    "price_lkr",
    "guest_capacity",
    "rating",
    "review_count",
    "popularity_score"
]


# =====================================================
# 8. PREPROCESSING
# =====================================================

preprocessor = ColumnTransformer(

    transformers=[

        (
            "categorical",

            OneHotEncoder(
                handle_unknown="ignore"
            ),

            categorical_features
        )

    ],

    remainder="passthrough"
)


# =====================================================
# 9. RANDOM FOREST
# =====================================================

model = RandomForestRegressor(

    n_estimators=100,

    random_state=42,

    n_jobs=-1
)


# =====================================================
# 10. CREATE PIPELINE
# =====================================================

pipeline = Pipeline(

    steps=[

        (
            "preprocessor",
            preprocessor
        ),

        (
            "model",
            model
        )

    ]
)


# =====================================================
# 11. TRAIN / TEST SPLIT
# =====================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,

    y,

    test_size=0.20,

    random_state=42
)


print()
print("====================================")
print("DATA SPLIT")
print("====================================")

print()
print(
    "Training records:",
    len(X_train)
)

print(
    "Testing records:",
    len(X_test)
)


# =====================================================
# 12. TRAIN MODEL
# =====================================================

print()
print("====================================")
print("MODEL TRAINING")
print("====================================")

print()
print("Training Random Forest model...")

pipeline.fit(
    X_train,
    y_train
)

print(
    "Training completed successfully!"
)


# =====================================================
# 13. PREDICTIONS
# =====================================================

predictions = pipeline.predict(
    X_test
)


# =====================================================
# 14. MODEL EVALUATION
# =====================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

r2 = r2_score(
    y_test,
    predictions
)


print()
print("====================================")
print("MODEL EVALUATION")
print("====================================")

print(
    "Mean Absolute Error:",
    round(mae, 2)
)

print(
    "R2 Score:",
    round(r2, 3)
)


# =====================================================
# 15. SAVE MODEL
# =====================================================

joblib.dump(
    pipeline,
    MODEL_PATH
)


print()
print("====================================")
print("MODEL SAVED")
print("====================================")

print()
print("Saved model to:")

print(
    MODEL_PATH
)


# =====================================================
# 16. FINAL TRAINING CHECK
# =====================================================

print()
print("====================================")
print("TRAINING COMPLETE")
print("====================================")

print()
print("Dataset used:")
print(
    DATASET_PATH.name
)

print()
print("Records used:")
print(
    len(data)
)

print()
print("Model:")
print(
    MODEL_PATH.name
)