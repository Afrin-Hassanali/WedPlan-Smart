import pandas as pd
import joblib

from pathlib import Path

from database import get_connection


# =====================================================
# 1. FIND MODEL
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATH = (
    BASE_DIR
    / "model"
    / "wedplan_recommendation_model.pkl"
)


# =====================================================
# 2. CHECK MODEL
# =====================================================

if not MODEL_PATH.exists():

    raise FileNotFoundError(
        f"Model file not found:\n{MODEL_PATH}"
    )


# =====================================================
# 3. LOAD TRAINED ML MODEL
# =====================================================

model = joblib.load(
    MODEL_PATH
)


# =====================================================
# 4. LOAD VENDORS FROM MYSQL
# =====================================================
#
# IMPORTANT:
# The recommendation system now uses the
# SAME 2,000 vendor records stored in MySQL.
#
# It no longer reads the Excel dataset
# during recommendation.
#
# Excel is still used for MODEL TRAINING.
# MySQL is used for LIVE APPLICATION DATA.
#
# =====================================================

def load_vendors_from_mysql():

    connection = get_connection()

    cursor = connection.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
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
                suitability_score,
                created_at
            FROM vendors
            """
        )

        rows = cursor.fetchall()

        return pd.DataFrame(rows)

    finally:

        cursor.close()

        connection.close()


# =====================================================
# 5. LOAD VENDORS
# =====================================================

vendors = load_vendors_from_mysql()


# =====================================================
# 6. CHECK VENDOR DATA
# =====================================================

if vendors.empty:

    raise ValueError(
        "No vendors found in the MySQL vendors table."
    )


print(
    "===================================="
)

print(
    "WEDPLAN SMART RECOMMENDATION SYSTEM"
)

print(
    "===================================="
)

print()

print(
    "Vendor records loaded from MySQL:",
    len(vendors)
)

print()


# =====================================================
# 7. CLEAN DATA
# =====================================================

vendors["location"] = (
    vendors["location"]
    .astype(str)
    .str.strip()
)

vendors["category"] = (
    vendors["category"]
    .astype(str)
    .str.strip()
)

vendors["available"] = (
    vendors["available"]
    .astype(str)
    .str.strip()
)

vendors["price_basis"] = (
    vendors["price_basis"]
    .astype(str)
    .str.strip()
)

vendors["wedding_style"] = (
    vendors["wedding_style"]
    .astype(str)
    .str.strip()
)


# =====================================================
# 8. NUMERIC DATA CLEANING
# =====================================================

numeric_columns = [

    "price_lkr",

    "guest_capacity",

    "rating",

    "review_count",

    "popularity_score",

    "suitability_score"

]


for column in numeric_columns:

    vendors[column] = pd.to_numeric(

        vendors[column],

        errors="coerce"

    )


# =====================================================
# 9. RECOMMENDATION FUNCTION
# =====================================================

def get_recommendations(

    location,

    wedding_style,

    guest_count,

    budget,

    selected_services=None

):

    # =================================================
    # ALWAYS GET CURRENT VENDORS FROM MYSQL
    # =================================================
    #
    # This is intentional.
    #
    # If an Admin adds/edits a vendor in MySQL,
    # the recommendation system can use the
    # updated information.
    #
    # =================================================

    data = load_vendors_from_mysql()


    # =================================================
    # CHECK DATA
    # =================================================

    if data.empty:

        return pd.DataFrame()


    # =================================================
    # CLEAN CURRENT DATA
    # =================================================

    data["location"] = (

        data["location"]

        .astype(str)

        .str.strip()

    )


    data["category"] = (

        data["category"]

        .astype(str)

        .str.strip()

    )


    data["available"] = (

        data["available"]

        .astype(str)

        .str.strip()

    )


    data["price_basis"] = (

        data["price_basis"]

        .astype(str)

        .str.strip()

    )


    data["wedding_style"] = (

        data["wedding_style"]

        .astype(str)

        .str.strip()

    )


    for column in numeric_columns:

        data[column] = pd.to_numeric(

            data[column],

            errors="coerce"

        )


    # =================================================
    # CONVERT INPUTS
    # =================================================

    location = str(
        location
    ).strip()

    wedding_style = str(
        wedding_style
    ).strip()

    guest_count = int(
        guest_count
    )

    budget = float(
        budget
    )


    # =================================================
    # LOCATION FILTER
    # =================================================

    if location:

        data = data[

            data["location"]
            .str.lower()
            ==
            location.lower()

        ]

        if data.empty:

            return pd.DataFrame()


    # =================================================
    # WEDDING STYLE FILTER
    # =================================================

    if wedding_style:

        data = data[

            data["wedding_style"]
            .str.lower()
            ==
            wedding_style.lower()

        ]

        if data.empty:

            return pd.DataFrame()


    # =================================================
    # AVAILABILITY FILTER
    # =================================================

    data = data[

        data["available"]
        .str.lower()
        ==
        "yes"

    ]


    if data.empty:

        return pd.DataFrame()


    # =================================================
    # SERVICE FILTER
    # =================================================

    if selected_services:

        service_mapping = {

            "Venue": "Venue",

            "Catering": "Catering",

            "Photography": "Photography",

            "Videography": "Videography",

            "Decoration": "Decoration"

        }


        selected_categories = [

            service_mapping[service]

            for service in selected_services

            if service in service_mapping

        ]


        if selected_categories:

            data = data[

                data["category"].isin(

                    selected_categories

                )

            ]


            if data.empty:

                return pd.DataFrame()


    # =================================================
    # GUEST CAPACITY FILTER
    # =================================================
    #
    # Guest capacity is mainly important for venues.
    #
    # Other services can still be recommended
    # for larger weddings.
    #
    # =================================================

    if "Venue" in data["category"].values:

        venue_mask = (

            data["category"]
            .str.lower()
            ==
            "venue"

        )


        suitable_venue_mask = (

            (

                data["guest_capacity"]

                >=

                guest_count

            )

            |

            (

                data["guest_capacity"]

                ==

                0

            )

        )


        data = data[

            (~venue_mask)

            |

            suitable_venue_mask

        ]


    # =================================================
    # CHECK AFTER CAPACITY FILTER
    # =================================================

    if data.empty:

        return pd.DataFrame()


    # =================================================
    # ESTIMATED COST
    # =================================================

    def calculate_cost(row):

        price_basis = (

            str(
                row["price_basis"]
            )

            .strip()

            .lower()

        )


        if price_basis == "per_guest":

            return (

                float(
                    row["price_lkr"]
                )

                *

                guest_count

            )


        return float(

            row["price_lkr"]

        )


    data = data.copy()


    data["estimated_cost"] = data.apply(

        calculate_cost,

        axis=1

    )


    # =================================================
    # INDIVIDUAL BUDGET FILTER
    # =================================================

    data = data[

        data["estimated_cost"]

        <=

        budget

    ]


    if data.empty:

        return pd.DataFrame()


    # =================================================
    # ML FEATURES
    # =================================================
    #
    # THESE MUST MATCH THE FEATURES USED
    # WHEN THE RANDOM FOREST MODEL WAS TRAINED.
    #
    # =================================================

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


    prediction_data = data[

        features

    ].copy()


    # =================================================
    # HANDLE MISSING NUMERIC VALUES
    # =================================================

    prediction_data["price_lkr"] = (

        prediction_data["price_lkr"]

        .fillna(0)

    )


    prediction_data["guest_capacity"] = (

        prediction_data["guest_capacity"]

        .fillna(0)

    )


    prediction_data["rating"] = (

        prediction_data["rating"]

        .fillna(0)

    )


    prediction_data["review_count"] = (

        prediction_data["review_count"]

        .fillna(0)

    )


    prediction_data["popularity_score"] = (

        prediction_data["popularity_score"]

        .fillna(0)

    )


    prediction_data["category"] = (

        prediction_data["category"]

        .fillna("")

    )


    prediction_data["location"] = (

        prediction_data["location"]

        .fillna("")

    )


    prediction_data["wedding_style"] = (

        prediction_data["wedding_style"]

        .fillna("")

    )


    prediction_data["available"] = (

        prediction_data["available"]

        .fillna("")

    )


    # =================================================
    # RANDOM FOREST PREDICTION
    # =================================================

    data["suitability_score"] = (

        model.predict(

            prediction_data

        )

    )


    # =================================================
    # LIMIT SCORE
    # =================================================

    data["suitability_score"] = (

        data["suitability_score"]

        .clip(

            0,

            100

        )

        .round(1)

    )


    # =================================================
    # STYLE MATCH
    # =================================================

    if wedding_style:

        data["style_match"] = (

            data["wedding_style"]

            .str.lower()

            ==

            wedding_style.lower()

        ).astype(int)

    else:

        data["style_match"] = 0


    # =================================================
    # FINAL RECOMMENDATION SCORE
    # =================================================

    data["recommendation_score"] = (

        data["suitability_score"]

        +

        (

            data["style_match"]

            *

            2

        )

    ).clip(

        0,

        100

    ).round(1)


    # =================================================
    # SORT RECOMMENDATIONS
    # =================================================

    data = data.sort_values(

        by=[

            "recommendation_score",

            "suitability_score",

            "rating"

        ],

        ascending=[

            False,

            False,

            False

        ]

    )


    # =================================================
    # RETURN TOP 10
    # =================================================

    return data.head(10)