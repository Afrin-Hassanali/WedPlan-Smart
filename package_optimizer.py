import pandas as pd
import joblib

from pathlib import Path

from ml.recommendation import get_recommendations


# =====================================================
# 1. FIND PROJECT FILES
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

DATASET_PATH = (
    BASE_DIR
    / "dataset"
    / "WedPlan_Smart_Training_Starter_Dataset.xlsx"
)

MODEL_PATH = (
    BASE_DIR
    / "model"
    / "wedplan_recommendation_model.pkl"
)


# =====================================================
# 2. CHECK FILES
# =====================================================

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"\nDataset not found:\n{DATASET_PATH}"
    )

if not MODEL_PATH.exists():
    raise FileNotFoundError(
        f"\nModel not found:\n{MODEL_PATH}"
    )


# =====================================================
# 3. LOAD DATASET
# =====================================================

vendors = pd.read_excel(
    DATASET_PATH,
    sheet_name="Training_Data"
)


# =====================================================
# 4. LOAD TRAINED ML MODEL
# =====================================================

model = joblib.load(
    MODEL_PATH
)


# =====================================================
# 5. CLEAN DATA
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

vendors["wedding_style"] = (
    vendors["wedding_style"]
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


# =====================================================
# 6. CALCULATE VENDOR COST
# =====================================================

def calculate_vendor_cost(vendor, guest_count):

    price_basis = (
        str(vendor["price_basis"])
        .strip()
        .lower()
    )

    if price_basis == "per_guest":

        return (
            float(vendor["price_lkr"])
            * guest_count
        )

    return float(
        vendor["price_lkr"]
    )


# =====================================================
# 7. MULTIPLE-CHOICE KNAPSACK OPTIMIZER
# =====================================================

def optimize_package(
    service_options,
    selected_services,
    budget
):
    """
    Multiple-Choice Knapsack Optimization.

    Each selected service represents one group.

    Exactly one vendor is selected from each service.

    Objective:
        Maximize total recommendation score.

    Constraint:
        Total package cost must not exceed the
        user's available budget.
    """

    # -------------------------------------------------
    # Convert budget into LKR 100 units
    # -------------------------------------------------

    UNIT = 100

    budget_units = int(
        budget // UNIT
    )

    # -------------------------------------------------
    # DP state
    #
    # Key:
    #     cost_units
    #
    # Value:
    #     {
    #         score,
    #         cost,
    #         package
    #     }
    # -------------------------------------------------

    states = {
        0: {
            "score": 0.0,
            "cost": 0.0,
            "package": []
        }
    }

    # -------------------------------------------------
    # Process each service
    # -------------------------------------------------

    for service in selected_services:

        options = service_options[service]

        new_states = {}

        # ---------------------------------------------
        # Try every vendor for this service
        # ---------------------------------------------

        for current_units, current_state in states.items():

            for vendor in options:

                vendor_cost = float(
                    vendor["estimated_cost"]
                )

                vendor_score = float(
                    vendor["recommendation_score"]
                )

                new_cost = (
                    current_state["cost"]
                    + vendor_cost
                )

                # -------------------------------------
                # Budget constraint
                # -------------------------------------

                if new_cost > budget:
                    continue

                new_units = int(
                    new_cost // UNIT
                )

                new_score = (
                    current_state["score"]
                    + vendor_score
                )

                new_package = (
                    current_state["package"]
                    + [vendor]
                )

                # -------------------------------------
                # Keep the best state for this cost
                # -------------------------------------

                if new_units not in new_states:

                    new_states[new_units] = {
                        "score": new_score,
                        "cost": new_cost,
                        "package": new_package
                    }

                else:

                    existing = (
                        new_states[new_units]
                    )

                    # Higher recommendation score wins
                    if new_score > existing["score"]:

                        new_states[new_units] = {
                            "score": new_score,
                            "cost": new_cost,
                            "package": new_package
                        }

                    # If scores are equal,
                    # choose cheaper package
                    elif (
                        new_score
                        == existing["score"]
                        and new_cost
                        < existing["cost"]
                    ):

                        new_states[new_units] = {
                            "score": new_score,
                            "cost": new_cost,
                            "package": new_package
                        }

        states = new_states

        # -------------------------------------------------
        # If no valid state remains
        # -------------------------------------------------

        if not states:
            return None

    # =================================================
    # SELECT BEST FINAL PACKAGE
    # =================================================

    best_state = None

    for state in states.values():

        if best_state is None:

            best_state = state

        elif state["score"] > best_state["score"]:

            best_state = state

        elif (
            state["score"]
            == best_state["score"]
            and state["cost"]
            < best_state["cost"]
        ):

            best_state = state

    return best_state


# =====================================================
# 8. GENERATE WEDDING PACKAGE
# =====================================================

def generate_wedding_package(
    budget,
    guest_count,
    location,
    wedding_style,
    selected_services
):

    budget = float(budget)

    guest_count = int(guest_count)

    location = str(
        location
    ).strip()

    wedding_style = str(
        wedding_style
    ).strip()

    # Remove duplicate services
    selected_services = list(
        dict.fromkeys(
            selected_services
        )
    )

    # =================================================
    # VALIDATE SERVICES
    # =================================================

    if not selected_services:

        return {
            "success": False,
            "reason": "NO_SERVICES_SELECTED",

            "message": (
                "Please select at least one "
                "wedding service."
            ),

            "package": [],
            "total_cost": 0,
            "remaining_budget": budget,
            "budget": budget,

            "guest_count": guest_count,
            "location": location,
            "wedding_style": wedding_style,

            "shortfall": 0,
            "cheapest_package_cost": None,

            "missing_services": [],

            "suggestions": [
                "Select at least one wedding service."
            ]
        }

    # =================================================
    # SERVICE OPTIONS
    # =================================================

    service_options = {}

    unavailable_services = []

    # =================================================
    # GET RECOMMENDATIONS FOR EACH SERVICE
    # =================================================

    for service in selected_services:

        print()
        print(
            f"Checking {service} vendors..."
        )

        recommendations = get_recommendations(

            location=location,

            wedding_style=wedding_style,

            guest_count=guest_count,

            budget=budget,

            selected_services=[
                service
            ]
        )

        # =================================================
        # NO VENDORS
        # =================================================

        if recommendations.empty:

            unavailable_services.append(
                service
            )

            print(
                f"No suitable {wedding_style} "
                f"{service} vendors matched "
                f"the current requirements."
            )

            continue

        # =================================================
        # COPY RESULTS
        # =================================================

        recommendations = (
            recommendations.copy()
        )

        # =================================================
        # CALCULATE ESTIMATED COST
        # =================================================

        recommendations[
            "estimated_cost"
        ] = recommendations.apply(

            lambda row:
            calculate_vendor_cost(
                row,
                guest_count
            ),

            axis=1
        )

        # =================================================
        # KEEP VENDORS THAT FIT INDIVIDUAL BUDGET
        # =================================================

        recommendations = (
            recommendations[
                recommendations[
                    "estimated_cost"
                ] <= budget
            ]
        )

        if recommendations.empty:

            unavailable_services.append(
                service
            )

            print(
                f"{service} vendors were found, "
                f"but none individually fit "
                f"within the available budget."
            )

            continue

        # =================================================
        # SORT RECOMMENDATIONS
        # =================================================

        recommendations = (

            recommendations

            .sort_values(

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

            .head(10)
        )

        # =================================================
        # STORE OPTIONS
        # =================================================

        service_options[service] = (
            recommendations.to_dict(
                orient="records"
            )
        )

        print(
            f"{service}: "
            f"{len(service_options[service])} "
            f"matching vendors found."
        )

    # =================================================
    # CHECK UNAVAILABLE SERVICES
    # =================================================

    if unavailable_services:

        missing_text = ", ".join(
            unavailable_services
        )

        return {

            "success": False,

            "reason": "SERVICE_UNAVAILABLE",

            "message": (
                f"No suitable vendor option "
                f"was available for: "
                f"{missing_text}."
            ),

            "package": [],

            "total_cost": 0,

            "remaining_budget": budget,

            "budget": budget,

            "guest_count": guest_count,

            "location": location,

            "wedding_style": wedding_style,

            "shortfall": 0,

            "cheapest_package_cost": None,

            "missing_services":
                unavailable_services,

            "suggestions": [
                "Try another location.",
                "Try another wedding style.",
                "Increase your budget.",
                "Reduce the number of guests.",
                "Remove the unavailable service."
            ]
        }

    # =================================================
    # CHEAPEST POSSIBLE PACKAGE
    # =================================================

    print()
    print(
        "======================================"
    )

    print(
        "CHEAPEST OPTIONS BY SERVICE"
    )

    print(
        "======================================"
    )

    cheapest_total = 0

    for service in selected_services:

        options = service_options[
            service
        ]

        cheapest = min(

            options,

            key=lambda vendor:
            float(
                vendor[
                    "estimated_cost"
                ]
            )
        )

        cheapest_cost = float(
            cheapest[
                "estimated_cost"
            ]
        )

        print(
            f"{service}: "
            f"{cheapest['vendor_name']} "
            f"-> LKR "
            f"{cheapest_cost:,.2f}"
        )

        cheapest_total += (
            cheapest_cost
        )

    print(
        "--------------------------------------"
    )

    print(
        "CHEAPEST POSSIBLE PACKAGE: "
        f"LKR {cheapest_total:,.2f}"
    )

    print(
        "AVAILABLE BUDGET: "
        f"LKR {budget:,.2f}"
    )

    print(
        "--------------------------------------"
    )

    # =================================================
    # BUDGET FAILURE
    # =================================================

    if cheapest_total > budget:

        shortfall = (
            cheapest_total
            - budget
        )

        print()
        print(
            "======================================"
        )

        print(
            "BUDGET LIMIT EXCEEDED"
        )

        print(
            "======================================"
        )

        print(
            f"Budget: "
            f"LKR {budget:,.2f}"
        )

        print(
            f"Cheapest complete package: "
            f"LKR {cheapest_total:,.2f}"
        )

        print(
            f"Additional budget required: "
            f"LKR {shortfall:,.2f}"
        )

        return {

            "success": False,

            "reason": "PACKAGE_OVER_BUDGET",

            "message": (
                "Suitable vendors were found "
                "for all selected services, "
                "but the complete package "
                "exceeds the available budget."
            ),

            "package": [],

            "total_cost": 0,

            "remaining_budget": budget,

            "budget": budget,

            "guest_count": guest_count,

            "location": location,

            "wedding_style": wedding_style,

            "cheapest_package_cost":
                round(
                    cheapest_total,
                    2
                ),

            "shortfall":
                round(
                    shortfall,
                    2
                ),

            "missing_services": [],

            "suggestions": [
                "Increase your budget.",
                "Reduce the number of guests.",
                "Change your selected services.",
                "Try another location.",
                "Try another wedding style."
            ]
        }

    # =================================================
    # MULTIPLE-CHOICE KNAPSACK
    # =================================================

    print()
    print(
        "======================================"
    )

    print(
        "MULTIPLE-CHOICE KNAPSACK OPTIMIZATION"
    )

    print(
        "======================================"
    )

    print(
        "Objective: Maximize recommendation score"
    )

    print(
        "Constraint: Total cost <= available budget"
    )

    print(
        "Each selected service: Exactly one vendor"
    )

    # =================================================
    # OPTIMIZE
    # =================================================

    best_state = optimize_package(

        service_options=service_options,

        selected_services=selected_services,

        budget=budget
    )

    # =================================================
    # NO VALID PACKAGE
    # =================================================

    if best_state is None:

        return {

            "success": False,

            "reason": "NO_PACKAGE",

            "message": (
                "Suitable vendors were found, "
                "but no complete combination "
                "of the selected services could "
                "be created within the budget."
            ),

            "package": [],

            "total_cost": 0,

            "remaining_budget": budget,

            "budget": budget,

            "guest_count": guest_count,

            "location": location,

            "wedding_style": wedding_style,

            "cheapest_package_cost":
                round(
                    cheapest_total,
                    2
                ),

            "shortfall":
                max(
                    0,
                    round(
                        cheapest_total
                        - budget,
                        2
                    )
                ),

            "missing_services": [],

            "suggestions": [
                "Increase your budget.",
                "Reduce the number of guests.",
                "Change your selected services.",
                "Try another location.",
                "Try another wedding style."
            ]
        }

    # =================================================
    # GET OPTIMIZED PACKAGE
    # =================================================

    best_package = (
        best_state["package"]
    )

    best_total_cost = float(
        best_state["cost"]
    )

    best_score = float(
        best_state["score"]
    )

    # =================================================
    # FORMAT PACKAGE
    # =================================================

    package = []

    for vendor in best_package:

        package.append({

            "vendor_id": int(
                vendor["vendor_id"]
            ),

            "vendor_name":
                vendor["vendor_name"],

            "category":
                vendor["category"],

            "location":
                vendor["location"],

            "price_lkr":
                float(
                    vendor["price_lkr"]
                ),

            "price_basis":
                vendor["price_basis"],

            "estimated_cost":
                round(
                    float(
                        vendor[
                            "estimated_cost"
                        ]
                    ),
                    2
                ),

            "rating":
                float(
                    vendor["rating"]
                ),

            "suitability_score":
                round(
                    float(
                        vendor[
                            "suitability_score"
                        ]
                    ),
                    1
                ),

            "style_match":
                int(
                    vendor["style_match"]
                ),

            "recommendation_score":
                round(
                    float(
                        vendor[
                            "recommendation_score"
                        ]
                    ),
                    1
                )
        })

    # =================================================
    # REMAINING BUDGET
    # =================================================

    remaining_budget = (
        budget
        -
        best_total_cost
    )

    # =================================================
    # SUCCESS RESULT
    # =================================================

    return {

        "success": True,

        "reason": "SUCCESS",

        "message": (
            "A suitable wedding package "
            "was successfully created."
        ),

        "package": package,

        "total_cost":
            round(
                best_total_cost,
                2
            ),

        "remaining_budget":
            round(
                remaining_budget,
                2
            ),

        "budget":
            budget,

        "guest_count":
            guest_count,

        "location":
            location,

        "wedding_style":
            wedding_style,

        "within_budget":
            True,

        "cheapest_package_cost":
            round(
                cheapest_total,
                2
            ),

        "shortfall":
            0,

        "missing_services": [],

        "suggestions": [],

        "optimization_score":
            round(
                best_score,
                2
            )
    }


# =====================================================
# 9. TEST PROGRAM
# =====================================================

if __name__ == "__main__":

    # =================================================
    # TEST INPUT
    # =================================================

    test_budget = 3000000

    test_guest_count = 350

    test_location = "Colombo"

    test_wedding_style = "Traditional"

    test_services = [

        "Venue",

        "Catering",

        "Photography",

        "Videography",

        "Decoration"
    ]

    # =================================================
    # DISPLAY HEADER
    # =================================================

    print()

    print(
        "======================================"
    )

    print(
        "WEDPLAN SMART PACKAGE OPTIMIZER"
    )

    print(
        "======================================"
    )

    print()

    print(
        "Dataset:"
    )

    print(
        DATASET_PATH
    )

    print()

    print(
        "Total vendor records loaded:"
    )

    print(
        len(vendors)
    )

    # =================================================
    # DISPLAY TEST INPUT
    # =================================================

    print()

    print(
        "======================================"
    )

    print(
        "       TEST INPUT"
    )

    print(
        "======================================"
    )

    print(
        "Budget:",
        f"LKR {test_budget:,.2f}"
    )

    print(
        "Guests:",
        test_guest_count
    )

    print(
        "Location:",
        test_location
    )

    print(
        "Wedding Style:",
        test_wedding_style
    )

    print(
        "Services:",
        test_services
    )

    # =================================================
    # GENERATE PACKAGE
    # =================================================

    result = generate_wedding_package(

        budget=test_budget,

        guest_count=test_guest_count,

        location=test_location,

        wedding_style=test_wedding_style,

        selected_services=test_services
    )

    # =================================================
    # DISPLAY RESULT
    # =================================================

    print()

    print(
        "======================================"
    )

    print(
        "      WEDPLAN SMART AI PACKAGE"
    )

    print(
        "======================================"
    )

    # =================================================
    # SUCCESS
    # =================================================

    if result["success"]:

        print()

        print(
            "OPTIMIZED WEDDING PACKAGE"
        )

        print(
            "--------------------------------------"
        )

        print(
            f"Location: "
            f"{result['location']}"
        )

        print(
            f"Wedding Style: "
            f"{result['wedding_style']}"
        )

        print(
            f"Guests: "
            f"{result['guest_count']}"
        )

        print(
            "--------------------------------------"
        )

        for item in result["package"]:

            print(
                f"Category: "
                f"{item['category']}"
            )

            print(
                f"Vendor: "
                f"{item['vendor_name']}"
            )

            print(
                f"Estimated Cost: "
                f"LKR "
                f"{item['estimated_cost']:,.2f}"
            )

            print(
                f"ML Suitability Score: "
                f"{item['suitability_score']}"
            )

            print(
                f"Style Match: "
                f"{item['style_match']}"
            )

            print(
                f"Recommendation Score: "
                f"{item['recommendation_score']}"
            )

            print(
                f"Rating: "
                f"{item['rating']}"
            )

            print(
                "--------------------------------------"
            )

        print(
            f"\nTotal Cost: "
            f"LKR "
            f"{result['total_cost']:,.2f}"
        )

        print(
            f"Remaining Budget: "
            f"LKR "
            f"{result['remaining_budget']:,.2f}"
        )

        print(
            f"Within Budget: "
            f"{result['within_budget']}"
        )

        print(
            f"Optimization Score: "
            f"{result['optimization_score']}"
        )

    # =================================================
    # FAILURE
    # =================================================

    else:

        print()

        print(
            "PACKAGE COULD NOT BE CREATED"
        )

        print(
            "--------------------------------------"
        )

        print(
            f"Reason: "
            f"{result['reason']}"
        )

        print()

        print(
            result["message"]
        )

        # ---------------------------------------------
        # BUDGET INFORMATION
        # ---------------------------------------------

        if (
            result["reason"]
            == "PACKAGE_OVER_BUDGET"
        ):

            print()

            print(
                f"Your Budget: "
                f"LKR "
                f"{result['budget']:,.2f}"
            )

            print(
                f"Cheapest Complete Package: "
                f"LKR "
                f"{result['cheapest_package_cost']:,.2f}"
            )

            print(
                f"Additional Budget Required: "
                f"LKR "
                f"{result['shortfall']:,.2f}"
            )

        # ---------------------------------------------
        # MISSING SERVICES
        # ---------------------------------------------

        if result[
            "missing_services"
        ]:

            print()

            print(
                "Unavailable Services:"
            )

            for missing_service in result[
                "missing_services"
            ]:

                print(
                    f"- {missing_service}"
                )

        # ---------------------------------------------
        # SUGGESTIONS
        # ---------------------------------------------

        if result["suggestions"]:

            print()

            print(
                "SUGGESTIONS:"
            )

            for suggestion in result[
                "suggestions"
            ]:

                print(
                    f"- {suggestion}"
                )