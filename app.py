
from flask import Flask, render_template, request, redirect, session, flash
import re
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error

from database import get_connection
from ml.package_optimizer import generate_wedding_package


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(__name__)

import os

app.secret_key = os.environ.get(
    "SECRET_KEY",
    "wedplan_smart_secret_key"
)

# =====================================================
# PASSWORD HELPER
# =====================================================

def verify_password(stored_password, entered_password):

    if not stored_password:
        return False

    # New hashed passwords
    try:

        if check_password_hash(
            stored_password,
            entered_password
        ):
            return True

    except Exception:
        pass

    # Old plaintext passwords
    return stored_password == entered_password


def valid_gmail(email):
    return re.fullmatch(
        r"[a-z0-9][a-z0-9._%+-]*@gmail\.com",
        email
    ) is not None


# =====================================================
# USER AUTHENTICATION
# =====================================================

def user_required():

    if session.get("role") != "user":
        return redirect("/login")

    return None


# =====================================================
# ADMIN AUTHENTICATION
# =====================================================

def admin_required():

    if session.get("role") != "admin":
        return redirect("/login")

    return None


# =====================================================
# GLOBAL PLAN STATUS
# =====================================================

@app.context_processor
def inject_plan_status():

    has_plan = False

    if session.get("role") == "user":
        connection = None
        cursor = None

        try:
            connection = get_connection()
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT booking_id
                FROM bookings
                WHERE user_id = %s
                ORDER BY booking_id DESC
                LIMIT 1
                """,
                (session.get("user_id"),)
            )

            has_plan = cursor.fetchone() is not None

        except Exception:
            has_plan = False

        finally:
            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

            try:
                if connection:
                    connection.close()
            except Exception:
                pass

    return {"has_plan": has_plan}


# =====================================================
# HOME
# =====================================================

@app.route("/")
def home():

    print("================================")
    print("LOADING HOME INDEX.HTML")
    print("================================")

    return render_template("index.html")


# =====================================================
# REGISTER
# =====================================================

@app.route(
    "/register",
    methods=["GET", "POST"]
)
def register():

    if request.method == "POST":

        fullname = request.form.get(
            "fullname",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not valid_gmail(email):
            return """
            <script>
                alert("Please enter a valid Gmail address ending with @gmail.com.");
                window.location.href = "/register";
            </script>
            """

        password = request.form.get(
            "password",
            ""
        )

        if not fullname:

            return """
            <script>
                alert("Please enter your full name.");
                window.location.href="/register";
            </script>
            """

        if not email:

            return """
            <script>
                alert("Please enter your email.");
                window.location.href="/register";
            </script>
            """

        if not password:

            return """
            <script>
                alert("Please enter a password.");
                window.location.href="/register";
            </script>
            """

        if len(password) < 6:

            return """
            <script>
                alert("Password must contain at least 6 characters.");
                window.location.href="/register";
            </script>
            """

        connection = None
        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor(
                dictionary=True
            )

            # Check duplicate email

            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                LIMIT 1
                """,
                (
                    email,
                )
            )

            existing_user = cursor.fetchone()

            if existing_user:

                return """
                <script>
                    alert("An account with this email already exists.");
                    window.location.href="/login";
                </script>
                """

            cursor.execute(
                """
                SELECT admin_id
                FROM admins
                WHERE email = %s
                LIMIT 1
                """,
                (email,)
            )

            if cursor.fetchone():
                return """
                <script>
                    alert("This email is reserved for administrator login.");
                    window.location.href = "/login";
                </script>
                """

            password_hash = generate_password_hash(
                password
            )

            cursor.execute(
                """
                INSERT INTO users
                (
                    full_name,
                    email,
                    password
                )
                VALUES
                (
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    fullname,
                    email,
                    password_hash
                )
            )

            connection.commit()

            return """
            <script>
                alert("Account created successfully. Please login.");
                window.location.href="/login";
            </script>
            """

        except Error as e:

            if connection:
                connection.rollback()

            print(
                "Registration error:",
                e
            )

            return """
            <script>
                alert("Registration failed. Please try again.");
                window.location.href="/register";
            </script>
            """

        finally:

            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

            try:
                if connection:
                    connection.close()
            except Exception:
                pass

    return render_template(
        "register.html"
    )


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        if not valid_gmail(email):
            return """
            <script>
                alert("Please enter a valid Gmail address ending with @gmail.com.");
                window.location.href = "/login";
            </script>
            """

        password = request.form.get(
            "password",
            ""
        )

        login_type = request.form.get(
            "login_type",
            "user"
        )

        # =================================================
        # USER LOGIN
        # =================================================

        if login_type == "user":

            connection = None
            cursor = None

            try:

                connection = get_connection()

                cursor = connection.cursor(
                    dictionary=True
                )

                cursor.execute(
                    """
                    SELECT
                        user_id,
                        full_name,
                        email,
                        password,
                        is_active
                    FROM users
                    WHERE email = %s
                    LIMIT 1
                    """,
                    (
                        email,
                    )
                )

                user = cursor.fetchone()

                if not user:

                    return """
                    <script>
                        alert("Invalid user email or password.");
                        window.location.href="/login";
                    </script>
                    """

                if not user["is_active"]:

                    return """
                    <script>
                        alert("Your account has been deactivated by the administrator.");
                        window.location.href="/login";
                    </script>
                    """

                if not verify_password(
                    user["password"],
                    password
                ):

                    return """
                    <script>
                        alert("Invalid user email or password.");
                        window.location.href="/login";
                    </script>
                    """

                # Upgrade old plaintext password

                try:

                    is_hashed = (
                        user["password"].startswith("scrypt:")
                        or
                        user["password"].startswith("pbkdf2:")
                    )

                    if not is_hashed:

                        new_hash = generate_password_hash(
                            password
                        )

                        cursor.execute(
                            """
                            UPDATE users
                            SET password = %s
                            WHERE user_id = %s
                            """,
                            (
                                new_hash,
                                user["user_id"]
                            )
                        )

                        connection.commit()

                except Exception as e:

                    print(
                        "Password upgrade warning:",
                        e
                    )

                session.clear()

                session["user_id"] = user["user_id"]

                session["fullname"] = user["full_name"]

                session["email"] = user["email"]

                session["role"] = "user"

                return redirect(
                    "/dashboard"
                )

            except Error as e:

                print(
                    "User login error:",
                    e
                )

                return """
                <script>
                    alert("Login failed. Please try again.");
                    window.location.href="/login";
                </script>
                """

            finally:

                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass

                try:
                    if connection:
                        connection.close()
                except Exception:
                    pass

        # =================================================
        # ADMIN LOGIN
        # =================================================

        elif login_type == "admin":

            connection = None
            cursor = None

            try:

                connection = get_connection()

                cursor = connection.cursor(
                    dictionary=True
                )

                cursor.execute(
                    """
                    SELECT
                        admin_id,
                        full_name,
                        email,
                        password,
                        is_active
                    FROM admins
                    WHERE email = %s
                    LIMIT 1
                    """,
                    (
                        email,
                    )
                )

                admin = cursor.fetchone()

                if not admin:

                    return """
                    <script>
                        alert("Invalid admin email or password.");
                        window.location.href="/login";
                    </script>
                    """

                if not admin["is_active"]:

                    return """
                    <script>
                        alert("This administrator account is inactive.");
                        window.location.href="/login";
                    </script>
                    """

                if not verify_password(
                    admin["password"],
                    password
                ):

                    return """
                    <script>
                        alert("Invalid admin email or password.");
                        window.location.href="/login";
                    </script>
                    """

                # Upgrade plaintext admin password

                try:

                    is_hashed = (
                        admin["password"].startswith("scrypt:")
                        or
                        admin["password"].startswith("pbkdf2:")
                    )

                    if not is_hashed:

                        new_hash = generate_password_hash(
                            password
                        )

                        cursor.execute(
                            """
                            UPDATE admins
                            SET password = %s
                            WHERE admin_id = %s
                            """,
                            (
                                new_hash,
                                admin["admin_id"]
                            )
                        )

                        connection.commit()

                except Exception as e:

                    print(
                        "Admin password upgrade warning:",
                        e
                    )

                session.clear()

                session["admin_id"] = admin["admin_id"]

                session["admin_name"] = admin["full_name"]

                session["email"] = admin["email"]

                session["role"] = "admin"

                return redirect(
                    "/admin"
                )

            except Error as e:

                print(
                    "Admin login error:",
                    e
                )

                return """
                <script>
                    alert("Admin login failed.");
                    window.location.href="/login";
                </script>
                """

            finally:

                try:
                    if cursor:
                        cursor.close()
                except Exception:
                    pass

                try:
                    if connection:
                        connection.close()
                except Exception:
                    pass

        else:

            return redirect(
                "/login"
            )

    return render_template(
        "login.html"
    )


# =====================================================
# FORGOT PASSWORD
# =====================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    # -------------------------------------------------
    # SHOW RESET PASSWORD PAGE
    # -------------------------------------------------

    if request.method == "GET":
        email = request.args.get("email", "")
        return render_template(
            "forgot_password.html",
            email=email
        )

    # -------------------------------------------------
    # GET FORM DATA
    # -------------------------------------------------

    email = (
        request.form.get(
            "email",
            ""
        )
        .strip()
        .lower()
    )

    new_password = request.form.get(
        "new_password",
        ""
    )

    confirm_password = request.form.get(
        "confirm_password",
        ""
    )


    # -------------------------------------------------
    # VALIDATE EMAIL
    # -------------------------------------------------

    if not valid_gmail(email):

        return """
        <script>
            alert(
                "Please enter a valid Gmail address ending with @gmail.com."
            );
            window.location.href = "/forgot-password";
        </script>
        """


    # -------------------------------------------------
    # VALIDATE PASSWORD
    # -------------------------------------------------

    if len(new_password) < 6:

        return """
        <script>
            alert(
                "Password must contain at least 6 characters."
            );
            window.location.href = "/forgot-password";
        </script>
        """


    # -------------------------------------------------
    # CHECK PASSWORD MATCH
    # -------------------------------------------------

    if new_password != confirm_password:

        return """
        <script>
            alert(
                "Passwords do not match."
            );
            window.location.href = "/forgot-password";
        </script>
        """


    connection = None
    cursor = None


    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )


        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                is_active
            FROM users
            WHERE LOWER(email) = %s
            LIMIT 1
            """,
            (
                email,
            )
        )


        user = cursor.fetchone()


        # -------------------------------------------------
        # EMAIL NOT FOUND
        # -------------------------------------------------

        if not user:

            return """
            <script>
                alert(
                    "No account was found with this email address."
                );
                window.location.href = "/forgot-password";
            </script>
            """


        # -------------------------------------------------
        # CHECK ACCOUNT STATUS
        # -------------------------------------------------

        if not user["is_active"]:

            return """
            <script>
                alert(
                    "Your account has been deactivated by the administrator."
                );
                window.location.href = "/login";
            </script>
            """


        # -------------------------------------------------
        # HASH NEW PASSWORD
        # -------------------------------------------------

        password_hash = generate_password_hash(
            new_password
        )


        # -------------------------------------------------
        # UPDATE PASSWORD
        # -------------------------------------------------

        cursor.execute(
            """
            UPDATE users
            SET password = %s
            WHERE user_id = %s
            """,
            (
                password_hash,
                user["user_id"]
            )
        )


        connection.commit()


        # -------------------------------------------------
        # SUCCESS
        # -------------------------------------------------

        return """
        <script>
            alert(
                "Password reset successfully. Please login with your new password."
            );
            window.location.href = "/login";
        </script>
        """


    except Error as e:

        if connection:

            connection.rollback()


        print(
            "Forgot password error:",
            e
        )


        return """
        <script>
            alert(
                "Something went wrong. Please try again."
            );
            window.location.href = "/forgot-password";
        </script>
        """


    finally:

        try:

            if cursor:
                cursor.close()

        except Exception:
            pass


        try:

            if connection:
                connection.close()

        except Exception:
            pass

# =====================================================
# DASHBOARD / CREATE WEDDING PLAN
# =====================================================

@app.route(
    "/dashboard",
    methods=["GET", "POST"]
)
def dashboard():

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    if request.method == "POST":

        # =================================================
        # GET FORM DATA
        # =================================================

        try:

            budget = float(
                request.form["budget"]
            )

            guest_count = int(
                request.form["guest_count"]
            )

            location = request.form[
                "location"
            ].strip()

            wedding_style = request.form[
                "wedding_style"
            ].strip()

            selected_services = request.form.getlist(
                "services"
            )

        except (
            ValueError,
            KeyError
        ):

            return """
            <script>
                alert("Please enter valid wedding details.");
                window.location.href="/dashboard";
            </script>
            """

        # =================================================
        # VALIDATION
        # =================================================

        if budget <= 0:

            return """
            <script>
                alert("Budget must be greater than 0.");
                window.location.href="/dashboard";
            </script>
            """

        if guest_count <= 0:

            return """
            <script>
                alert("Guest count must be greater than 0.");
                window.location.href="/dashboard";
            </script>
            """

        if not location:

            return """
            <script>
                alert("Please select a location.");
                window.location.href="/dashboard";
            </script>
            """

        if not wedding_style:

            return """
            <script>
                alert("Please select a wedding style.");
                window.location.href="/dashboard";
            </script>
            """

        if not selected_services:

            return """
            <script>
                alert("Please select at least one wedding service.");
                window.location.href="/dashboard";
            </script>
            """

        services = ", ".join(
            selected_services
        )

        # =================================================
        # RUN AI PACKAGE OPTIMIZER FIRST
        # =================================================

        try:

            package_result = generate_wedding_package(
                budget=budget,
                guest_count=guest_count,
                location=location,
                wedding_style=wedding_style,
                selected_services=selected_services
            )

        except Exception as e:

            print(
                "AI package generation error:",
                e
            )

            return render_template(
                "result.html",
                booking=None,
                wedding_package=[],
                package=[],
                recommendations=[],
                budget=budget,
                guest_count=guest_count,
                location=location,
                wedding_style=wedding_style,
                total_cost=0,
                remaining_budget=budget,
                within_budget=False,
                error="The wedding package could not be generated.",
                error_reason="SYSTEM_ERROR",
                cheapest_package_cost=None,
                shortfall=0,
                missing_services=[],
                suggestions=[]
            )

        # =================================================
        # AI FAILURE
        # =================================================

        if not package_result.get(
            "success",
            False
        ):

            return render_template(
                "result.html",
                booking=None,
                wedding_package=[],
                package=[],
                recommendations=[],
                budget=budget,
                guest_count=guest_count,
                location=location,
                wedding_style=wedding_style,
                total_cost=0,
                remaining_budget=budget,
                within_budget=False,
                error=package_result.get(
                    "message",
                    "The wedding package could not be generated."
                ),
                error_reason=package_result.get(
                    "reason",
                    ""
                ),
                cheapest_package_cost=package_result.get(
                    "cheapest_package_cost"
                ),
                shortfall=package_result.get(
                    "shortfall",
                    0
                ),
                missing_services=package_result.get(
                    "missing_services",
                    []
                ),
                suggestions=package_result.get(
                    "suggestions",
                    []
                )
            )

        # =================================================
        # SUCCESSFUL AI PACKAGE
        # =================================================

        wedding_package = package_result[
            "package"
        ]

        # =================================================
        # DATABASE CONNECTION
        # =================================================

        connection = None
        cursor = None

        try:

            connection = get_connection()

            cursor = connection.cursor()

            # =================================================
            # SAVE BOOKING
            # =================================================

            cursor.execute(
                """
                INSERT INTO bookings
                (
                    user_id,
                    budget,
                    guest_count,
                    location,
                    wedding_style,
                    services
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    session["user_id"],
                    budget,
                    guest_count,
                    location,
                    wedding_style,
                    services
                )
            )

            booking_id = cursor.lastrowid

            # =================================================
            # SAVE RECOMMENDATIONS
            # =================================================

            for vendor in wedding_package:

                cursor.execute(
                    """
                    INSERT INTO recommendations
                    (
                        booking_id,
                        vendor_id,
                        suitability_score,
                        estimated_cost
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        booking_id,
                        vendor["vendor_id"],
                        vendor["suitability_score"],
                        vendor["estimated_cost"]
                    )
                )

            # =================================================
            # IMPORTANT:
            # CREATE PLANNED EXPENSES FROM AI PACKAGE
            # =================================================

            for vendor in wedding_package:

                cursor.execute(
                    """
                    INSERT INTO expenses
                    (
                        user_id,
                        booking_id,
                        category,
                        description,
                        planned_amount,
                        actual_amount,
                        expense_status
                    )
                    VALUES
                    (
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    """,
                    (
                        session["user_id"],
                        booking_id,
                        vendor["category"],
                        vendor["vendor_name"],
                        vendor["estimated_cost"],
                        0,
                        "Pending"
                    )
                )

            connection.commit()

        except Error as e:

            if connection:
                connection.rollback()

            print(
                "Wedding plan database error:",
                e
            )

            return """
            <script>
                alert("Unable to save your wedding plan. Please try again.");
                window.location.href="/dashboard";
            </script>
            """

        finally:

            try:
                if cursor:
                    cursor.close()
            except Exception:
                pass

            try:
                if connection:
                    connection.close()
            except Exception:
                pass

        # =================================================
        # SAVE SESSION DATA
        # =================================================

        session["current_budget"] = (
            budget
        )

        session["current_guest_count"] = (
            guest_count
        )

        session["current_location"] = (
            location
        )

        session["current_wedding_style"] = (
            wedding_style
        )

        session["current_booking_id"] = (
            booking_id
        )

        session["total_cost"] = (
            package_result["total_cost"]
        )

        session["remaining_budget"] = (
            package_result["remaining_budget"]
        )

        # =================================================
        # GO TO RESULT
        # =================================================

        return redirect(
            "/result"
        )

    return render_template(
        "dashboard.html"
    )


# =====================================================
# RESULT
# =====================================================

@app.route("/result")
def result():

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # LATEST BOOKING
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM bookings
            WHERE user_id = %s
            ORDER BY booking_id DESC
            LIMIT 1
            """,
            (
                session["user_id"],
            )
        )

        booking = cursor.fetchone()

        if not booking:

            return redirect(
                "/dashboard"
            )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                r.recommendation_id,
                r.booking_id,
                r.vendor_id,
                r.suitability_score,
                r.estimated_cost,

                v.vendor_name,
                v.category,
                v.location,
                v.price_lkr,
                v.price_basis,
                v.guest_capacity,
                v.rating

            FROM recommendations r

            INNER JOIN vendors v
                ON r.vendor_id = v.vendor_id

            WHERE r.booking_id = %s

            ORDER BY
                FIELD(
                    v.category,
                    'Venue',
                    'Catering',
                    'Photography',
                    'Videography',
                    'Decoration'
                )
            """,
            (
                booking["booking_id"],
            )
        )

        recommendations = cursor.fetchall()

    except Error as e:

        print(
            "Result database error:",
            e
        )

        return redirect(
            "/dashboard"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    budget = float(
        booking["budget"]
    )

    guest_count = int(
        booking["guest_count"]
    )

    location = booking[
        "location"
    ]

    wedding_style = booking[
        "wedding_style"
    ]

    total_cost = sum(
        float(
            item["estimated_cost"]
        )
        for item in recommendations
    )

    remaining_budget = (
        budget - total_cost
    )

    within_budget = (
        remaining_budget >= 0
    )

    return render_template(
        "result.html",
        booking=booking,
        wedding_package=recommendations,
        package=recommendations,
        recommendations=recommendations,
        budget=budget,
        guest_count=guest_count,
        location=location,
        wedding_style=wedding_style,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        within_budget=within_budget,
        error=None
    )


# =====================================================
# ANALYTICS
# =====================================================

@app.route("/analytics")
def analytics():

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # LATEST BOOKING
        # =================================================

        cursor.execute(
            """
            SELECT *
            FROM bookings
            WHERE user_id = %s
            ORDER BY booking_id DESC
            LIMIT 1
            """,
            (
                session["user_id"],
            )
        )

        booking = cursor.fetchone()

        if not booking:

            return redirect(
                "/dashboard"
            )

        # =================================================
        # RECOMMENDATIONS
        # =================================================

        cursor.execute(
            """
            SELECT
                r.vendor_id,
                r.suitability_score,
                r.estimated_cost,
                v.vendor_name,
                v.category,
                v.location,
                v.rating,
                v.guest_capacity

            FROM recommendations r

            INNER JOIN vendors v
                ON r.vendor_id = v.vendor_id

            WHERE r.booking_id = %s

            ORDER BY
                FIELD(
                    v.category,
                    'Venue',
                    'Catering',
                    'Photography',
                    'Videography',
                    'Decoration'
                )
            """,
            (
                booking["booking_id"],
            )
        )

        recommendations = cursor.fetchall()

    except Error as e:

        print(
            "Analytics error:",
            e
        )

        return redirect(
            "/dashboard"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    budget = float(
        booking["budget"]
    )

    guest_count = int(
        booking["guest_count"]
    )

    location = booking[
        "location"
    ] or ""

    total_cost = sum(
        float(
            item["estimated_cost"]
        )
        for item in recommendations
    )

    remaining_budget = (
        budget - total_cost
    )

    if guest_count > 0:

        per_guest_cost = (
            total_cost / guest_count
        )

    else:

        per_guest_cost = 0

    within_budget = (
        total_cost <= budget
    )

    categories = []

    for item in recommendations:

        cost = float(
            item["estimated_cost"]
        )

        if total_cost > 0:

            share = (
                cost / total_cost
            ) * 100

        else:

            share = 0

        categories.append(
            {
                "category": item["category"],
                "vendor": item["vendor_name"],
                "cost": cost,
                "share": share
            }
        )

    chart_colors = [
        "#D1A455",
        "#E596BD",
        "#55329A",
        "#7FA8C9",
        "#8FAF91"
    ]

    chart_angles = []

    current_angle = 0

    for category in categories:

        current_angle += (
            category["share"] * 3.6
        )

        chart_angles.append(
            current_angle
        )

    while len(chart_angles) < 5:

        chart_angles.append(
            360
        )

    return render_template(
        "analytics.html",
        booking=booking,
        recommendations=recommendations,
        categories=categories,
        budget=budget,
        guest_count=guest_count,
        location=location,
        total_cost=total_cost,
        remaining_budget=remaining_budget,
        per_guest_cost=per_guest_cost,
        within_budget=within_budget,
        chart_colors=chart_colors,
        chart_angles=chart_angles
    )


# =====================================================
# EXPENSE TRACKING
# =====================================================

@app.route("/expenses")
def expenses():

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    user_id = session.get(
        "user_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # GET CURRENT / LATEST WEDDING PLAN
        # =================================================

        cursor.execute(
            """
            SELECT
                booking_id,
                budget,
                guest_count,
                location,
                wedding_style,
                services

            FROM bookings

            WHERE user_id = %s

            ORDER BY booking_id DESC

            LIMIT 1
            """,
            (
                user_id,
            )
        )

        booking = cursor.fetchone()

        # =================================================
        # NO PLAN
        # =================================================

        if not booking:

            flash(
                "Please generate your wedding plan before tracking expenses.",
                "error"
            )

            return redirect(
                "/dashboard"
            )

        booking_id = booking[
            "booking_id"
        ]

        # =================================================
        # GET EXPENSES FOR THIS PLAN
        # =================================================

        cursor.execute(
            """
            SELECT
                expense_id,
                booking_id,
                category,
                description,
                planned_amount,
                actual_amount,
                expense_status,
                created_at

            FROM expenses

            WHERE user_id = %s

            AND booking_id = %s

            ORDER BY
                created_at ASC
            """,
            (
                user_id,
                booking_id
            )
        )

        expense_rows = cursor.fetchall()

        # =================================================
        # ACTUAL SPENDING
        # =================================================

        cursor.execute(
            """
            SELECT
                COALESCE(
                    SUM(actual_amount),
                    0
                ) AS total_actual

            FROM expenses

            WHERE user_id = %s

            AND booking_id = %s
            """,
            (
                user_id,
                booking_id
            )
        )

        total_result = cursor.fetchone()

        total_actual = float(
            total_result[
                "total_actual"
            ] or 0
        )

        # =================================================
        # BUDGET
        # =================================================

        budget = float(
            booking["budget"]
        )

        remaining = (
            budget - total_actual
        )

        return render_template(
            "expenses.html",
            expenses=expense_rows,
            budget=budget,
            total_actual=total_actual,
            remaining=remaining,
            booking=booking
        )

    except Error as e:

        print(
            "Expense page database error:",
            e
        )

        flash(
            "Unable to load expenses.",
            "error"
        )

        return redirect(
            "/dashboard"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass


# =====================================================
# ADD EXPENSE
# =====================================================

@app.route(
    "/expenses/add",
    methods=["POST"]
)
def add_expense():

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    user_id = session.get(
        "user_id"
    )

    category = request.form.get(
        "category",
        ""
    ).strip()

    description = request.form.get(
        "description",
        ""
    ).strip()

    expense_status = request.form.get(
        "expense_status",
        "Pending"
    ).strip()

    allowed_statuses = [
        "Paid",
        "Pending",
        "Partially Paid"
    ]

    if expense_status not in allowed_statuses:

        expense_status = "Pending"

    try:

        planned_amount = float(
            request.form.get(
                "planned_amount",
                0
            ) or 0
        )

        actual_amount = float(
            request.form.get(
                "actual_amount",
                0
            ) or 0
        )

    except (
        TypeError,
        ValueError
    ):

        flash(
            "Please enter valid expense amounts.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    if not category:

        flash(
            "Please select an expense category.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    if planned_amount < 0:

        flash(
            "Planned amount cannot be negative.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    if actual_amount < 0:

        flash(
            "Actual amount cannot be negative.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # CURRENT BOOKING
        # =================================================

        cursor.execute(
            """
            SELECT booking_id
            FROM bookings
            WHERE user_id = %s
            ORDER BY booking_id DESC
            LIMIT 1
            """,
            (
                user_id,
            )
        )

        booking = cursor.fetchone()

        if not booking:

            flash(
                "Please generate your wedding plan before adding expenses.",
                "error"
            )

            return redirect(
                "/dashboard"
            )

        booking_id = booking[
            "booking_id"
        ]

        # =================================================
        # INSERT EXPENSE
        # =================================================

        cursor.execute(
            """
            INSERT INTO expenses
            (
                user_id,
                booking_id,
                category,
                description,
                planned_amount,
                actual_amount,
                expense_status
            )
            VALUES
            (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            )
            """,
            (
                user_id,
                booking_id,
                category,
                description,
                planned_amount,
                actual_amount,
                expense_status
            )
        )

        connection.commit()

        flash(
            "Expense added successfully.",
            "success"
        )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Add expense error:",
            e
        )

        flash(
            "Unable to add expense.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/expenses"
    )


# =====================================================
# UPDATE EXPENSE
# =====================================================

@app.route(
    "/expenses/update/<int:expense_id>",
    methods=["POST"]
)
def update_expense(expense_id):

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    user_id = session.get(
        "user_id"
    )

    try:

        actual_amount = float(
            request.form.get(
                "actual_amount",
                0
            ) or 0
        )

    except (
        TypeError,
        ValueError
    ):

        flash(
            "Please enter a valid actual amount.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    if actual_amount < 0:

        flash(
            "Actual amount cannot be negative.",
            "error"
        )

        return redirect(
            "/expenses"
        )

    expense_status = request.form.get(
        "expense_status",
        "Pending"
    ).strip()

    allowed_statuses = [
        "Paid",
        "Pending",
        "Partially Paid"
    ]

    if expense_status not in allowed_statuses:

        expense_status = "Pending"

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE expenses

            SET
                actual_amount = %s,
                expense_status = %s

            WHERE expense_id = %s

            AND user_id = %s
            """,
            (
                actual_amount,
                expense_status,
                expense_id,
                user_id
            )
        )

        connection.commit()

        if cursor.rowcount > 0:

            flash(
                "Expense updated successfully.",
                "success"
            )

        else:

            flash(
                "Expense not found.",
                "error"
            )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Update expense error:",
            e
        )

        flash(
            "Unable to update expense.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/expenses"
    )


# =====================================================
# DELETE EXPENSE
# =====================================================

@app.route(
    "/expenses/delete/<int:expense_id>",
    methods=["POST"]
)
def delete_expense(
    expense_id
):

    if session.get("role") != "user":

        return redirect(
            "/login"
        )

    user_id = session.get(
        "user_id"
    )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM expenses

            WHERE expense_id = %s

            AND user_id = %s
            """,
            (
                expense_id,
                user_id
            )
        )

        connection.commit()

        if cursor.rowcount > 0:

            flash(
                "Expense deleted successfully.",
                "success"
            )

        else:

            flash(
                "Expense not found.",
                "error"
            )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Delete expense error:",
            e
        )

        flash(
            "Unable to delete expense.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/expenses"
    )


# =====================================================
# ADMIN DASHBOARD
# =====================================================

@app.route("/admin")
def admin():

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        # =================================================
        # TOTAL VENDORS
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total_vendors
            FROM vendors
            """
        )

        total_result = cursor.fetchone()

        total_vendors = (
            total_result["total_vendors"]
            if total_result
            else 0
        )

        # =================================================
        # AVERAGE RATING
        # =================================================

        cursor.execute(
            """
            SELECT AVG(rating) AS avg_rating
            FROM vendors
            """
        )

        rating_result = cursor.fetchone()

        avg_rating = (
            float(
                rating_result["avg_rating"]
            )
            if rating_result
            and rating_result["avg_rating"] is not None
            else 0
        )

        # =================================================
        # CATEGORY COUNTS
        # =================================================

        cursor.execute(
            """
            SELECT
                category,
                COUNT(*) AS total
            FROM vendors
            GROUP BY category
            """
        )

        category_rows = cursor.fetchall()

        category_counts = {}

        for row in category_rows:

            category_counts[
                row["category"]
            ] = row["total"]

        # =================================================
        # ALL VENDORS
        # =================================================

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
                suitability_score

            FROM vendors

            ORDER BY vendor_id ASC
            """
        )

        vendors = cursor.fetchall()

        return render_template(
            "admin.html",
            total_vendors=total_vendors,
            avg_rating=avg_rating,
            category_counts=category_counts,
            vendors=vendors
        )

    except Error as e:

        print(
            "Admin error:",
            e
        )

        return """
        <h2>Admin database error</h2>
        <p>Please check the MySQL connection.</p>
        """

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass


# =====================================================
# ADMIN USER MANAGEMENT
# =====================================================

@app.route("/admin/users")
def admin_users():

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                email,
                phone,
                is_active,
                created_at

            FROM users

            ORDER BY created_at DESC
            """
        )

        users = cursor.fetchall()

        total_users = len(
            users
        )

        active_users = sum(
            1
            for user in users
            if user["is_active"]
        )

        inactive_users = (
            total_users - active_users
        )

        return render_template(
            "admin_users.html",
            users=users,
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users
        )

    except Error as e:

        print(
            "Admin users error:",
            e
        )

        return redirect(
            "/admin"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass


# =====================================================
# TOGGLE USER
# =====================================================

@app.route(
    "/admin/toggle-user/<int:user_id>",
    methods=["POST"]
)
def toggle_user(user_id):

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

        cursor.execute(
            """
            SELECT
                user_id,
                full_name,
                is_active

            FROM users

            WHERE user_id = %s
            """,
            (
                user_id,
            )
        )

        user = cursor.fetchone()

        if not user:

            flash(
                "User not found.",
                "error"
            )

            return redirect(
                "/admin/users"
            )

        new_status = (
            0
            if user["is_active"]
            else 1
        )

        cursor.execute(
            """
            UPDATE users

            SET is_active = %s

            WHERE user_id = %s
            """,
            (
                new_status,
                user_id
            )
        )

        connection.commit()

        if new_status:

            flash(
                f'{user["full_name"]} has been activated successfully.',
                "success"
            )

        else:

            flash(
                f'{user["full_name"]} has been deactivated successfully.',
                "success"
            )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Toggle user error:",
            e
        )

        flash(
            "Unable to update user status.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/admin/users"
    )


# =====================================================
# ADD VENDOR
# =====================================================

@app.route(
    "/admin/add-vendor",
    methods=["POST"]
)
def add_vendor():

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    try:

        vendor_name = request.form[
            "vendor_name"
        ].strip()

        category = request.form[
            "category"
        ]

        location = request.form[
            "location"
        ]

        price_lkr = float(
            request.form[
                "price_lkr"
            ]
        )

        price_basis = request.form.get(
            "price_basis",
            "package"
        )

        rating = float(
            request.form[
                "rating"
            ]
        )

        guest_capacity = int(
            request.form[
                "guest_capacity"
            ]
        )

        wedding_style = request.form.get(
            "wedding_style",
            ""
        ).strip()

        service_features = request.form.get(
            "service_features",
            ""
        ).strip()

    except (
        KeyError,
        ValueError
    ):

        flash(
            "Please enter valid vendor details.",
            "error"
        )

        return redirect(
            "/admin"
        )

    if not vendor_name:

        flash(
            "Vendor name is required.",
            "error"
        )

        return redirect(
            "/admin"
        )

    if price_lkr < 0:

        flash(
            "Price cannot be negative.",
            "error"
        )

        return redirect(
            "/admin"
        )

    if rating < 0 or rating > 5:

        flash(
            "Rating must be between 0 and 5.",
            "error"
        )

        return redirect(
            "/admin"
        )

    if guest_capacity < 0:

        flash(
            "Guest capacity cannot be negative.",
            "error"
        )

        return redirect(
            "/admin"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO vendors
            (
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
                %s
            )
            """,
            (
                vendor_name,
                category,
                location,
                price_lkr,
                price_basis,
                guest_capacity,
                rating,
                0,
                wedding_style,
                service_features,
                0.00,
                "Yes",
                0.00
            )
        )

        connection.commit()

        flash(
            "Vendor added successfully.",
            "success"
        )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Add vendor error:",
            e
        )

        flash(
            "Unable to add vendor.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/admin"
    )


# =====================================================
# DELETE VENDOR
# =====================================================

@app.route(
    "/admin/delete-vendor/<int:vendor_id>",
    methods=["POST"]
)
def delete_vendor(vendor_id):

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor()

        cursor.execute(
            """
            DELETE FROM vendors

            WHERE vendor_id = %s
            """,
            (
                vendor_id,
            )
        )

        connection.commit()

        if cursor.rowcount > 0:

            flash(
                "Vendor deleted successfully.",
                "success"
            )

        else:

            flash(
                "Vendor not found.",
                "error"
            )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Delete vendor error:",
            e
        )

        flash(
            "Unable to delete vendor. It may be linked to an existing recommendation.",
            "error"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass

    return redirect(
        "/admin"
    )


# =====================================================
# EDIT VENDOR
# =====================================================

@app.route(
    "/admin/edit-vendor/<int:vendor_id>",
    methods=["GET", "POST"]
)
def edit_vendor(vendor_id):

    if session.get("role") != "admin":

        return redirect(
            "/login"
        )

    connection = None
    cursor = None

    try:

        connection = get_connection()

        cursor = connection.cursor(
            dictionary=True
        )

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
                wedding_style,
                service_features

            FROM vendors

            WHERE vendor_id = %s
            """,
            (
                vendor_id,
            )
        )

        vendor = cursor.fetchone()

        if not vendor:

            return redirect(
                "/admin"
            )

        if request.method == "POST":

            try:

                vendor_name = request.form.get(
                    "vendor_name",
                    ""
                ).strip()

                category = request.form.get(
                    "category",
                    ""
                )

                location = request.form.get(
                    "location",
                    ""
                )

                price_lkr = float(
                    request.form.get(
                        "price_lkr",
                        0
                    )
                )

                price_basis = request.form.get(
                    "price_basis",
                    "package"
                )

                guest_capacity = int(
                    request.form.get(
                        "guest_capacity",
                        0
                    )
                )

                rating = float(
                    request.form.get(
                        "rating",
                        0
                    )
                )

                wedding_style = request.form.get(
                    "wedding_style",
                    ""
                ).strip()

                service_features = request.form.get(
                    "service_features",
                    ""
                ).strip()

            except (
                ValueError,
                TypeError
            ):

                flash(
                    "Please enter valid vendor details.",
                    "error"
                )

                return redirect(
                    f"/admin/edit-vendor/{vendor_id}"
                )

            if not vendor_name:

                flash(
                    "Vendor name is required.",
                    "error"
                )

                return redirect(
                    f"/admin/edit-vendor/{vendor_id}"
                )

            if price_lkr < 0:

                flash(
                    "Price cannot be negative.",
                    "error"
                )

                return redirect(
                    f"/admin/edit-vendor/{vendor_id}"
                )

            if guest_capacity < 0:

                flash(
                    "Guest capacity cannot be negative.",
                    "error"
                )

                return redirect(
                    f"/admin/edit-vendor/{vendor_id}"
                )

            if rating < 0 or rating > 5:

                flash(
                    "Rating must be between 0 and 5.",
                    "error"
                )

                return redirect(
                    f"/admin/edit-vendor/{vendor_id}"
                )

            cursor.execute(
                """
                UPDATE vendors

                SET
                    vendor_name = %s,
                    category = %s,
                    location = %s,
                    price_lkr = %s,
                    price_basis = %s,
                    guest_capacity = %s,
                    rating = %s,
                    wedding_style = %s,
                    service_features = %s

                WHERE vendor_id = %s
                """,
                (
                    vendor_name,
                    category,
                    location,
                    price_lkr,
                    price_basis,
                    guest_capacity,
                    rating,
                    wedding_style,
                    service_features,
                    vendor_id
                )
            )

            connection.commit()

            flash(
                "Vendor updated successfully.",
                "success"
            )

            return redirect(
                "/admin"
            )

        return render_template(
            "edit_vendor.html",
            vendor=vendor
        )

    except Error as e:

        if connection:
            connection.rollback()

        print(
            "Edit vendor error:",
            e
        )

        flash(
            "Unable to edit vendor.",
            "error"
        )

        return redirect(
            "/admin"
        )

    finally:

        try:
            if cursor:
                cursor.close()
        except Exception:
            pass

        try:
            if connection:
                connection.close()
        except Exception:
            pass


# =====================================================
# NAVIGATION COMPATIBILITY ROUTES
# =====================================================

@app.route("/wedding-planner")
@app.route("/ai-planner")
def wedding_planner():
    access = user_required()
    if access:
        return access
    return redirect("/dashboard")


@app.route("/packages")
def packages():
    access = user_required()
    if access:
        return access
    return redirect("/result")


@app.route("/guests")
def guests():
    access = user_required()
    if access:
        return access
    flash("Guest management is not available yet.", "info")
    return redirect("/dashboard")


@app.route("/checklist")
def checklist():
    access = user_required()
    if access:
        return access
    flash("Checklist is not available yet.", "info")
    return redirect("/dashboard")


# =====================================================
# LOGOUT
# =====================================================

@app.route("/logout")
def logout():

    session.clear()

    return redirect(
        "/login"
    )


# =====================================================
# RUN APPLICATION
# =====================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        port=5001
    )
