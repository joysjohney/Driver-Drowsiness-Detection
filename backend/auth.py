"""
========================================================
Authentication Module
--------------------------------------------------------
This module handles user authentication and management
for the Driver Drowsiness Detection System.

Main Responsibilities:
1. Register new users (driver or admin)
2. Login authentication
3. Logout functionality
4. Maintain user session
5. Fetch current logged-in user

Database Used:
users.db (SQLite)

Tables:
users
========================================================
"""

import sqlite3
import os

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash


# -------------------------------------------------------
# Database Path
# -------------------------------------------------------

DB_PATH = os.path.join(os.path.dirname(__file__), "users.db")


# -------------------------------------------------------
# Initialize Database (with mobile_number column)
# -------------------------------------------------------

def init_db():
    """
    Creates users table if it does not already exist.
    Adds mobile_number column if missing (for backward compatibility).
    """

    with sqlite3.connect(DB_PATH) as conn:

        # Create table if not exists
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            vehicle_number TEXT,
            mobile_number TEXT UNIQUE
        )
        """)

        # Check if mobile_number column exists; if not, add it
        cursor = conn.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        if "mobile_number" not in columns:
            conn.execute("ALTER TABLE users ADD COLUMN mobile_number TEXT")
            conn.commit()
            print("Added mobile_number column to users table.")

        # Add UNIQUE index on mobile_number if it doesn't exist yet
        existing_indexes = [
            row[1] for row in conn.execute("PRAGMA index_list(users)").fetchall()
        ]
        if "idx_users_mobile_number" not in existing_indexes:
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_mobile_number ON users(mobile_number)"
            )
            conn.commit()
            print("Added unique index on mobile_number.")

        conn.commit()


# Initialize database automatically
init_db()


# -------------------------------------------------------
# User Model Class
# -------------------------------------------------------

class User:
    """
    User model used for interacting with the users table.
    """

    def __init__(self, id, fullname, email, password, role, vehicle_number, mobile_number):
        self.id = id
        self.fullname = fullname
        self.email = email
        self.password = password
        self.role = role
        self.vehicle_number = vehicle_number
        self.mobile_number = mobile_number


    # ---------------------------------------------------
    # Create New User
    # ---------------------------------------------------

    @staticmethod
    def create(fullname, email, password, role, vehicle_number=None, mobile_number=None):

        hashed_password = generate_password_hash(password)

        try:
            with sqlite3.connect(DB_PATH) as conn:

                cursor = conn.execute("""
                INSERT INTO users (fullname, email, password, role, vehicle_number, mobile_number)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (fullname, email, hashed_password, role, vehicle_number, mobile_number))

                conn.commit()

                return User(
                    cursor.lastrowid,
                    fullname,
                    email,
                    hashed_password,
                    role,
                    vehicle_number,
                    mobile_number
                ), None

        except sqlite3.IntegrityError as e:
            err_msg = str(e).lower()
            if "mobile_number" in err_msg:
                return None, "Mobile number already registered"
            return None, "Email already registered"


    # ---------------------------------------------------
    # Find User by Email
    # ---------------------------------------------------

    @staticmethod
    def find_by_email(email):

        with sqlite3.connect(DB_PATH) as conn:

            conn.row_factory = sqlite3.Row

            row = conn.execute("""
            SELECT * FROM users WHERE email=?
            """, (email,)).fetchone()

            if row:
                return User(**row)

        return None


    # ---------------------------------------------------
    # Find User by ID
    # ---------------------------------------------------

    @staticmethod
    def find_by_id(user_id):

        with sqlite3.connect(DB_PATH) as conn:

            conn.row_factory = sqlite3.Row

            row = conn.execute("""
            SELECT * FROM users WHERE id=?
            """, (user_id,)).fetchone()

            if row:
                return User(**row)

        return None


    # ---------------------------------------------------
    # Get All Users (Admin Use)
    # ---------------------------------------------------

    @staticmethod
    def get_all():

        with sqlite3.connect(DB_PATH) as conn:

            conn.row_factory = sqlite3.Row

            rows = conn.execute("""
            SELECT * FROM users
            """).fetchall()

            return [User(**row).to_dict() for row in rows]


    # ---------------------------------------------------
    # Convert User Object to Dictionary
    # ---------------------------------------------------

    def to_dict(self):

        return {
            "id": self.id,
            "fullname": self.fullname,
            "email": self.email,
            "role": self.role,
            "vehicle_number": self.vehicle_number,
            "mobile_number": self.mobile_number
        }


    # ---------------------------------------------------
    # Password Check
    # ---------------------------------------------------

    def check_password(self, password):

        return check_password_hash(self.password, password)


    # ---------------------------------------------------
    # Update User Details
    # ---------------------------------------------------

    def update(self, **kwargs):

        fields = []
        values = []

        for key, value in kwargs.items():
            fields.append(f"{key}=?")
            values.append(value)
            setattr(self, key, value)

        if not fields:
            return

        values.append(self.id)

        sql = f"UPDATE users SET {', '.join(fields)} WHERE id=?"

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(sql, values)
            conn.commit()


    # ---------------------------------------------------
    # Delete User
    # ---------------------------------------------------

    def delete(self):

        with sqlite3.connect(DB_PATH) as conn:

            conn.execute("""
            DELETE FROM users WHERE id=?
            """, (self.id,))

            conn.commit()


# -------------------------------------------------------
# Flask Blueprint for Authentication
# -------------------------------------------------------

auth_bp = Blueprint("auth", __name__)


# -------------------------------------------------------
# Register New User
# -------------------------------------------------------

@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    fullname = data.get("fullname")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role")
    vehicle_number = data.get("vehicle_number")   # only for driver
    mobile_number = data.get("mobile")            # new field

    if not all([fullname, email, password, role, mobile_number]):
        return jsonify({"error": "Missing fields"}), 400

    user, error = User.create(fullname, email, password, role, vehicle_number, mobile_number)

    if error:
        return jsonify({"error": error}), 400

    return jsonify({"message": "User created successfully"}), 201


# -------------------------------------------------------
# Login Route
# -------------------------------------------------------

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400

    user = User.find_by_email(email)

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid credentials"}), 401

    # Store user info in session
    session["user_id"] = user.id
    session["role"] = user.role
    session["email"] = user.email

    return jsonify({
        "message": "Login successful",
        "role": user.role,
        "fullname": user.fullname
    })


# -------------------------------------------------------
# Logout Route
# -------------------------------------------------------

@auth_bp.route("/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({"message": "Logged out successfully"})


# -------------------------------------------------------
# Get Current Logged-in User
# -------------------------------------------------------

@auth_bp.route("/current_user", methods=["GET"])
def current_user():

    if "user_id" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = User.find_by_id(session["user_id"])

    if not user:
        return jsonify({"error": "User not found"}), 404

    return jsonify({
        "id": user.id,
        "fullname": user.fullname,
        "email": user.email,
        "role": user.role,
        "vehicle_number": user.vehicle_number if user.role == "user" else None,
        "mobile_number": user.mobile_number   # include in response
    })