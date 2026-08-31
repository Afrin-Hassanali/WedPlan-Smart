import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset.xlsx"
)


data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


venues = data[
    (
        data["category"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "venue"
    )
    &
    (
        data["location"]
        .astype(str)
        .str.strip()
        .str.lower()
        == "colombo"
    )
].copy()


print()
print("COLOMBO VENUE CAPACITY BY WEDDING STYLE")
print("========================================")


for style in [
    "Traditional",
    "Modern",
    "Luxury",
    "Beach",
    "Garden"
]:

    style_data = venues[
        venues["wedding_style"]
        .astype(str)
        .str.strip()
        .str.lower()
        == style.lower()
    ]


    print()
    print(f"{style}: {len(style_data)} venues")


    print(
        style_data[
            [
                "vendor_name",
                "guest_capacity",
                "price_lkr",
                "rating"
            ]
        ]
        .sort_values("guest_capacity")
        .to_string(index=False)
    )