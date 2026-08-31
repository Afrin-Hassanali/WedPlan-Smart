-- =========================================================
-- WEDPLAN SMART
-- DATABASE CREATION SCRIPT
-- AI-Based Wedding Budget Planning and Package
-- Recommendation System for Sri Lankan Weddings
-- =========================================================


-- =========================================================
-- CREATE DATABASE
-- =========================================================

CREATE DATABASE IF NOT EXISTS wedplan_smart;

USE wedplan_smart;


-- =========================================================
-- ADMINS TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS admins (

    admin_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    is_active TINYINT(1) NOT NULL DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


-- Verify admins table

SELECT *
FROM admins;


-- =========================================================
-- USERS TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS users (

    user_id INT AUTO_INCREMENT PRIMARY KEY,

    full_name VARCHAR(150) NOT NULL,

    email VARCHAR(150) NOT NULL UNIQUE,

    password VARCHAR(255) NOT NULL,

    phone VARCHAR(30),

    is_active TINYINT(1) NOT NULL DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


-- Verify users table

SELECT *
FROM users;


-- =========================================================
-- VENDORS TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS vendors (

    vendor_id INT AUTO_INCREMENT PRIMARY KEY,

    vendor_name VARCHAR(200) NOT NULL,

    category ENUM(
        'Venue',
        'Catering',
        'Photography',
        'Videography',
        'Decoration'
    ) NOT NULL,

    location VARCHAR(100) NOT NULL,

    price_lkr DECIMAL(12,2) NOT NULL,

    price_basis ENUM(
        'package',
        'per_guest'
    ) DEFAULT 'package',

    guest_capacity INT DEFAULT 0,

    rating DECIMAL(3,2) DEFAULT 0.00,

    review_count INT DEFAULT 0,

    wedding_style VARCHAR(150),

    service_features TEXT,

    popularity_score DECIMAL(5,2) DEFAULT 0.00,

    available ENUM(
        'Yes',
        'No'
    ) DEFAULT 'Yes',

    suitability_score DECIMAL(5,2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

);


-- Verify vendor data

SELECT COUNT(*) AS total_vendors
FROM vendors;

DESCRIBE vendors;

SELECT *
FROM vendors
LIMIT 5;


-- =========================================================
-- BOOKINGS TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS bookings (

    booking_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    budget DECIMAL(12,2) NOT NULL,

    guest_count INT NOT NULL,

    location VARCHAR(100) NOT NULL,

    wedding_style VARCHAR(100) NOT NULL,

    services TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE

);


-- Verify bookings table

DESCRIBE bookings;

SELECT *
FROM bookings;


-- =========================================================
-- RECOMMENDATIONS TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS recommendations (

    recommendation_id INT AUTO_INCREMENT PRIMARY KEY,

    booking_id INT NOT NULL,

    vendor_id INT NOT NULL,

    suitability_score DECIMAL(5,2) DEFAULT 0.00,

    estimated_cost DECIMAL(12,2) DEFAULT 0.00,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_recommendations_booking
        FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_recommendations_vendor
        FOREIGN KEY (vendor_id)
        REFERENCES vendors(vendor_id)
        ON DELETE CASCADE

);


-- Verify recommendations table

SELECT *
FROM recommendations;


-- =========================================================
-- EXPENSES TABLE
-- =========================================================

CREATE TABLE IF NOT EXISTS expenses (

    expense_id INT AUTO_INCREMENT PRIMARY KEY,

    user_id INT NOT NULL,

    booking_id INT NOT NULL,

    category VARCHAR(100) NOT NULL,

    description VARCHAR(255),

    planned_amount DECIMAL(12,2) DEFAULT 0.00,

    actual_amount DECIMAL(12,2) DEFAULT 0.00,

    expense_status VARCHAR(30) DEFAULT 'Pending',

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_expenses_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_expenses_booking
        FOREIGN KEY (booking_id)
        REFERENCES bookings(booking_id)
        ON DELETE CASCADE

);


-- =========================================================
-- DATABASE TABLE VERIFICATION
-- =========================================================

USE wedplan_smart;

SHOW TABLES;


-- =========================================================
-- TABLE STRUCTURE VERIFICATION
-- =========================================================

DESCRIBE admins;

DESCRIBE users;

DESCRIBE vendors;

DESCRIBE bookings;

DESCRIBE recommendations;

DESCRIBE expenses;


-- =========================================================
-- VENDOR STATISTICS
-- =========================================================

SELECT COUNT(*) AS total_vendors
FROM vendors;


SELECT
    category,
    COUNT(*) AS total
FROM vendors
GROUP BY category
ORDER BY category;


SELECT
    location,
    COUNT(*) AS total_vendors
FROM vendors
GROUP BY location
ORDER BY total_vendors DESC;


SELECT
    ROUND(AVG(rating), 2) AS average_rating
FROM vendors;


SELECT
    category,
    COUNT(*) AS total_vendors
FROM vendors
GROUP BY category;


-- =========================================================
-- USER INFORMATION
-- =========================================================

SELECT
    user_id,
    full_name,
    email,
    phone,
    is_active,
    created_at
FROM users;


-- =========================================================
-- ADMIN INFORMATION
-- =========================================================

SELECT
    admin_id,
    full_name,
    email,
    is_active,
    created_at
FROM admins;


-- =========================================================
-- BOOKING INFORMATION
-- =========================================================

SELECT
    booking_id,
    user_id,
    budget,
    guest_count,
    location,
    wedding_style,
    services,
    created_at
FROM bookings
ORDER BY booking_id DESC;


-- =========================================================
-- RECOMMENDATION INFORMATION
-- =========================================================

SELECT
    recommendation_id,
    booking_id,
    vendor_id,
    suitability_score,
    estimated_cost
FROM recommendations
ORDER BY recommendation_id DESC;


-- =========================================================
-- EXPENSE INFORMATION
-- =========================================================

SELECT
    expense_id,
    user_id,
    booking_id,
    category,
    description,
    planned_amount,
    actual_amount,
    expense_status,
    created_at
FROM expenses
ORDER BY expense_id DESC;


-- =========================================================
-- BOOKING + USER JOIN
-- =========================================================

SELECT
    b.booking_id,
    u.full_name,
    b.budget,
    b.guest_count,
    b.location,
    b.wedding_style
FROM bookings b
JOIN users u
    ON b.user_id = u.user_id
ORDER BY b.booking_id DESC;


-- =========================================================
-- RECOMMENDATION + VENDOR JOIN
-- =========================================================

SELECT
    r.recommendation_id,
    r.booking_id,
    v.vendor_name,
    v.category,
    v.location,
    r.suitability_score,
    r.estimated_cost
FROM recommendations r
JOIN vendors v
    ON r.vendor_id = v.vendor_id
ORDER BY r.recommendation_id DESC;


-- =========================================================
-- EXPENSE + USER JOIN
-- =========================================================

SELECT
    e.expense_id,
    u.full_name,
    e.booking_id,
    e.category,
    e.description,
    e.planned_amount,
    e.actual_amount,
    e.expense_status
FROM expenses e
JOIN users u
    ON e.user_id = u.user_id
ORDER BY e.expense_id DESC;


-- =========================================================
-- TOTAL ACTUAL SPENDING BY BOOKING
-- =========================================================

SELECT
    booking_id,
    SUM(actual_amount) AS total_actual_spending
FROM expenses
GROUP BY booking_id;


-- =========================================================
-- FINAL DATABASE VERIFICATION
-- =========================================================

USE wedplan_smart;

SHOW TABLES;


-- Total vendors

SELECT COUNT(*) AS total_vendors
FROM vendors;


-- Vendor ID range

SELECT
    MIN(vendor_id) AS minimum_vendor_id,
    MAX(vendor_id) AS maximum_vendor_id
FROM vendors;


-- Total users

SELECT COUNT(*) AS total_users
FROM users;


-- Total bookings

SELECT COUNT(*) AS total_bookings
FROM bookings;


-- Total recommendations

SELECT COUNT(*) AS total_recommendations
FROM recommendations;


-- Total expenses

SELECT COUNT(*) AS total_expenses
FROM expenses;


-- Total admins

SELECT COUNT(*) AS total_admins
FROM admins;


-- =========================================================
-- DEFAULT ADMIN ACCOUNT
-- =========================================================
-- This INSERT prevents a duplicate email error if the
-- script is executed again.

INSERT IGNORE INTO admins
(
    full_name,
    email,
    password,
    is_active
)
VALUES
(
    'WedPlan Administrator',
    'admin@gmail.com',
    'Admin@123',
    1
);


-- Verify administrator account

SELECT
    admin_id,
    full_name,
    email,
    is_active
FROM admins;


-- =========================================================
-- END OF WEDPLAN SMART DATABASE SCRIPT
-- =========================================================