import pandas as pd
import mysql.connector
from pathlib import Path


# =====================================================
# FIND DATASET
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset_OLD.xlsx"
)


print("Looking for dataset at:")
print(DATASET_PATH)


# =====================================================
# LOAD EXCEL DATASET
# =====================================================

data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


print()
print("Dataset loaded successfully!")
print("Total records:", len(data))


# =====================================================
# CONNECT TO MYSQL
# =====================================================

connection = mysql.connector.connect(

    host="localhost",

    user="wedplan_app",

    password="Afrin@123",

    database="wedplan_smart",

    port=3308

)

cursor = connection.cursor()


print()
print("Connected to MySQL successfully!")


# =====================================================
# INSERT VENDORS
# =====================================================

sql = """
INSERT INTO vendors
(
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
VALUES
(
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
"""


inserted = 0


for _, row in data.iterrows():

    values = (

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

        str(row["service_features"]),

        float(row["popularity_score"]),

        str(row["available"]),

        float(row["suitability_score"])

    )

    cursor.execute(
        sql,
        values
    )

    inserted += 1


# =====================================================
# SAVE CHANGES
# =====================================================

connection.commit()


print()
print("====================================")
print("VENDORS IMPORT COMPLETED")
print("====================================")
print("Records inserted:", inserted)


# =====================================================
# CLOSE CONNECTION
# =====================================================

cursor.close()

connection.close()


print()
print("MySQL connection closed.")