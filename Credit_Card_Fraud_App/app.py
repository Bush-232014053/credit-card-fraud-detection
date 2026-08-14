import os
import re
import json
import numpy as np
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from sklearn.ensemble import RandomForestClassifier

app = Flask(__name__)
app.secret_key = 'super_secret_fraudguard_key_12345'

# -------------------------------------------------------------
# Permanent User Storage
# -------------------------------------------------------------
USER_FILE = 'users.json'

def load_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users.json: {e}")
    
    default_users = {
        "abc@company.com": generate_password_hash("Abc@123"),
        "abc": generate_password_hash("Abc@123")
    }
    save_users(default_users)
    return default_users

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=4)


# -------------------------------------------------------------
# Train ML Model automatically from CSV File on Server Startup
# -------------------------------------------------------------
CSV_PATH = 'credit_card_fraud_1200_clean.csv'
model = None

if os.path.exists(CSV_PATH):
    try:
        # 1. Read CSV File
        df = pd.read_csv(CSV_PATH)
        
        # 2. Separate Features (X) and Target (y)
        # assuming the last column is the target (0 = Safe, 1 = Fraud)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        # 3. Train Random Forest Classifier in memory
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        print("✅ ML Model successfully trained in-memory from CSV file!")
        
    except Exception as e:
        print(f"⚠️ CSV file read/train error: {e}")
else:
    print("⚠️ CSV file not found! Fallback rule-based logic will be used.")


# Password Validation Function
def is_valid_password(password):
    if len(password) < 6:
        return False, "Password must be at least 6 characters long!"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)!"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)!"
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)!"
    return True, "Valid Password"


# 1. Landing Page
@app.route('/')
def home():
    return render_template('index.html')


# 2. Dashboard Page
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Session expired or unauthorized! Please sign in.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# 3. Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_user = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        users_db = load_users()
        stored_hash = users_db.get(email_or_user)

        if stored_hash and check_password_hash(stored_hash, password):
            session['user'] = email_or_user
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email/username or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# 4. Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        users_db = load_users()

        if email in users_db:
            flash('This email or username is already registered!', 'warning')
            return redirect(url_for('register'))

        is_valid, msg = is_valid_password(password)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('register'))

        users_db[email] = generate_password_hash(password)
        save_users(users_db)

        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# 5. Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# 6. AI Prediction Route
@app.route('/predict', methods=['POST'])
def predict():
    try:
        amount = float(request.form.get('Transaction_Amount', 0))
        time_since_last_tx = float(request.form.get('Time_Since_Last_Tx', 0))
        distance_from_last_tx = float(request.form.get('Distance_From_Last_Tx', 0))
        distance_from_home = float(request.form.get('Distance_From_Home', 0))
        daily_limit_used = float(request.form.get('Daily_Limit_Used', 0))
        card_age_days = float(request.form.get('Card_Age_Days', 0))

        features = np.array([[
            amount, time_since_last_tx, distance_from_last_tx,
            distance_from_home, daily_limit_used, card_age_days
        ]])

        if model is not None:
            prediction = model.predict(features)[0]
            is_fraud = bool(prediction == 1)
        else:
            is_fraud = (amount > 1000) or (daily_limit_used > 80) or (distance_from_home > 200)

        if is_fraud:
            return jsonify({'status': 'danger', 'prediction_text': '⚠️ Fraud Alert Detected!'})
        else:
            return jsonify({'status': 'success', 'prediction_text': '✅ Transaction Safe & Approved.'})

    except Exception as e:
        return jsonify({'status': 'danger', 'prediction_text': f"Server Error: {str(e)}"})


if __name__ == '__main__':
    app.run(debug=True)
    
