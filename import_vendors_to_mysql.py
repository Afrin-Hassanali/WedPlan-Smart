import pandas as pd
import mysql.connector
from pathlib import Path


# =====================================================
# 1. PROJECT PATH
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset.xlsx"
)


# =====================================================
# 2. CHECK DATASET
# =====================================================

if not DATASET_PATH.exists():

    raise FileNotFoundError(
        f"Dataset not found:\n{DATASET_PATH}"
    )


# =====================================================
# 3. LOAD EXCEL
# =====================================================

data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


print()
print("======================================")
print("WEDPLAN SMART MYSQL VENDOR IMPORT")
print("======================================")

print()
print("Dataset:")
print(DATASET_PATH)

print()
print("Excel records:")
print(len(data))


# =====================================================
# 4. REQUIRED COLUMNS
# =====================================================

required_columns = [

    "vendor_id",
    "vendor_name",
    "category",
    "location",
    "price_lkr",
    "price_basis",
    "guest_capacity",
    "rating",
    "review_count",
    "wedding_style",
    "service_features",
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
        "Missing dataset columns:\n"
        + "\n".join(missing_columns)
    )


# =====================================================
# 5. CONNECT TO MYSQL
# =====================================================

connection = mysql.connector.connect(
    host="localhost",
    port=3308,
    user="wedplan_app",
    password="WedPlanApp@2026",
    database="wedplan_smart"
)


cursor = connection.cursor()


print()
print("Connected to MySQL successfully.")


# =====================================================
# 6. UPSERT SQL
# =====================================================

sql = """

INSERT INTO vendors (

    vendor_id,
    vendor_name,
    category,
    location,
    price_lkr,
    price_basis,
    guest_capacity,
    rating,
    review_count,
    wedding_style,
    service_features,
    popularity_score,
    available,
    suitability_score

)

VALUES (

    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s,
    %s

)

ON DUPLICATE KEY UPDATE

    vendor_name = VALUES(vendor_name),

    category = VALUES(category),

    location = VALUES(location),

    price_lkr = VALUES(price_lkr),

    price_basis = VALUES(price_basis),

    guest_capacity = VALUES(guest_capacity),

    rating = VALUES(rating),

    review_count = VALUES(review_count),

    wedding_style = VALUES(wedding_style),

    service_features = VALUES(service_features),

    popularity_score = VALUES(popularity_score),

    available = VALUES(available),

    suitability_score = VALUES(suitability_score)

"""


# =====================================================
# 7. IMPORT DATA
# =====================================================

print()
print("Importing vendors...")
print()


count = 0


for _, row in data.iterrows():

    service_features = row["service_features"]

    if pd.isna(service_features):

        service_features = None

    else:

        service_features = str(
            service_features
        )


    cursor.execute(

        sql,

        (

            int(row["vendor_id"]),

            str(row["vendor_name"]),

            str(row["category"]),

            str(row["location"]),

            float(row["price_lkr"]),

            str(row["price_basis"]),

            int(row["guest_capacity"]),

            float(row["rating"]),

            int(row["review_count"]),

            str(row["wedding_style"]),

            service_features,

            float(row["popularity_score"]),

            str(row["available"]),

            float(row["suitability_score"])

        )

    )


    count += 1


    if count % 100 == 0:

        print(
            f"{count} records processed..."
        )


# =====================================================
# 8. COMMIT
# =====================================================

connection.commit()


# =====================================================
# 9. VERIFY
# =====================================================

cursor.execute(
    "SELECT COUNT(*) FROM vendors"
)

total_vendors = cursor.fetchone()[0]


cursor.execute(
    """
    SELECT
        MIN(vendor_id),
        MAX(vendor_id)
    FROM vendors
    """
)

min_id, max_id = cursor.fetchone()


# =====================================================
# 10. CLOSE
# =====================================================

cursor.close()

connection.close()


# =====================================================
# 11. RESULT
# =====================================================

print()
print("======================================")
print("MYSQL IMPORT COMPLETE")
print("======================================")

print()
print(
    "Excel records processed:",
    count
)

print(
    "Total vendors now in MySQL:",
    total_vendors
)

print(
    "Minimum vendor ID:",
    min_id
)

print(
    "Maximum vendor ID:",
    max_id
)

print()
print("SUCCESS!")