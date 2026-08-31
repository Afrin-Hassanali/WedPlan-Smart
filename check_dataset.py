import pandas as pd
from pathlib import Path


# =====================================================
# FIND PROJECT ROOT
# =====================================================

BASE_DIR = Path(__file__).resolve().parents[1]


# =====================================================
# USE THE NEW UPDATED DATASET
# =====================================================

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset.xlsx"
)


# =====================================================
# CHECK FILE
# =====================================================

if not DATASET_PATH.exists():

    raise FileNotFoundError(
        f"\nDataset not found:\n{DATASET_PATH}"
    )


# =====================================================
# LOAD DATASET
# =====================================================

data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


print()
print("========================================")
print("WEDPLAN SMART DATASET CHECK")
print("========================================")

print()
print("Dataset path:")
print(DATASET_PATH)

print()
print("TOTAL RECORDS:")
print(len(data))


# =====================================================
# WEDDING STYLE
# =====================================================

print()
print("WEDDING STYLE VALUES")
print("========================")

print(
    data["wedding_style"]
    .value_counts(dropna=False)
)


print()
print("UNIQUE VALUES:")

print(
    data["wedding_style"]
    .dropna()
    .unique()
)


# =====================================================
# SUITABILITY SCORE
# =====================================================

print()
print("SUITABILITY SCORE")
print("========================")

print(
    data["suitability_score"].describe()
)


# =====================================================
# SUITABILITY BY STYLE
# =====================================================

print()
print("SUITABILITY BY WEDDING STYLE")
print("========================")

print(
    data.groupby(
        "wedding_style"
    )["suitability_score"]
    .mean()
    .round(2)
)


# =====================================================
# SERVICE CATEGORY
# =====================================================

print()
print("SERVICE CATEGORY VALUES")
print("========================")

print(
    data["category"]
    .value_counts(dropna=False)
)


# =====================================================
# LOCATION
# =====================================================

print()
print("LOCATION VALUES")
print("========================")

print(
    data["location"]
    .value_counts(dropna=False)
)


# =====================================================
# VENUE CAPACITY CHECK
# =====================================================

print()
print("VENUE CAPACITY CHECK")
print("========================")

venues = data[
    data["category"]
    .astype(str)
    .str.strip()
    .str.lower()
    == "venue"
].copy()


print(
    "Total venue records:",
    len(venues)
)


print()
print("Capacity distribution:")

print(
    venues["guest_capacity"]
    .describe()
)


# =====================================================
# TRADITIONAL COLOMBO VENUE CHECK
# =====================================================

print()
print("TRADITIONAL + COLOMBO + VENUES")
print("========================")

traditional_colombo = venues[
    (
        venues["location"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "colombo"
    )
    &
    (
        venues["wedding_style"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "traditional"
    )
]


print(
    traditional_colombo[
        [
            "vendor_name",
            "guest_capacity",
            "price_lkr",
            "price_basis",
            "rating",
            "wedding_style"
        ]
    ]
    .sort_values(
        "guest_capacity"
    )
    .to_string(
        index=False
    )
)


# =====================================================
# CAPACITY TEST
# =====================================================

print()
print("CAPACITY AVAILABILITY TEST")
print("========================")

for guests in [
    150,
    250,
    350,
    450,
    550
]:

    suitable = traditional_colombo[
        traditional_colombo[
            "guest_capacity"
        ] >= guests
    ]

    print(
        f"{guests} guests: "
        f"{len(suitable)} suitable venue(s)"
    )