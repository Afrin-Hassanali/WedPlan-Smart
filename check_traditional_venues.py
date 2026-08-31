import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset_OLD.xlsx"
)


data = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


# Clean values
for column in [
    "location",
    "category",
    "wedding_style",
    "available"
]:
    data[column] = (
        data[column]
        .astype(str)
        .str.strip()
    )


print("\nTRADITIONAL COLOMBO VENUES")
print("==============================")

venues = data[
    (data["location"].str.lower() == "colombo")
    &
    (data["category"].str.lower() == "venue")
    &
    (data["wedding_style"].str.lower() == "traditional")
    &
    (data["available"].str.lower() == "yes")
]


print("Number of matching vendors:", len(venues))

print()

if venues.empty:

    print(
        "NO Traditional Colombo Venue "
        "vendors were found."
    )

else:

    print(
        venues[
            [
                "vendor_name",
                "price_lkr",
                "price_basis",
                "guest_capacity",
                "rating",
                "wedding_style"
            ]
        ].to_string(index=False)
    )