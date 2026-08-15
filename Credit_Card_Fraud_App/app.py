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

USER_FILE = 'users.json'

def load_users():
    """Load users from JSON file, with default pre-configured accounts"""
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users.json: {e}")
    
    default_users = {
        "bushraislam01933@gmail.com": generate_password_hash("Bushra@123"),
        "abc@company.com": generate_password_hash("Abc@123"),
        "abc": generate_password_hash("Abc@123")
    }
    save_users(default_users)
    return default_users

def save_users(users):
    """Save users dict to JSON file"""
    try:
        with open(USER_FILE, 'w') as f:
            json.dump(users, f, indent=4)
    except Exception as e:
        print(f"Error saving users: {e}")


# -------------------------------------------------------------
# Train ML Model automatically from CSV File on Server Startup
# -------------------------------------------------------------
CSV_PATH = 'credit_card_fraud_1200_clean.csv'
model = None

if os.path.exists(CSV_PATH):
    try:
        df = pd.read_csv(CSV_PATH)
        X = df.iloc[:, :-1]
        y = df.iloc[:, -1]
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X, y)
        print("✅ ML Model successfully trained in-memory from CSV!")
    except Exception as e:
        print(f"⚠️ CSV file read/train error: {e}")


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


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Session expired or unauthorized! Please sign in.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_user = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '').strip()

        users_db = load_users()
        
        matched_user_hash = None
        for key, stored_hash in users_db.items():
            if key.lower() == email_or_user:
                matched_user_hash = stored_hash
                break

        if matched_user_hash and check_password_hash(matched_user_hash, password):
            session['user'] = email_or_user
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email/username or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
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

        flash('Registration successful! Please sign in with your credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


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
            return jsonify({
                'status': 'danger',
                'prediction_text_bn': '⚠️ জালিয়াতি সংকেত চিহ্নিত হয়েছে!',
                'prediction_text_en': '⚠️ Fraud Alert Detected!'
            })
        else:
            return jsonify({
                'status': 'success',
                'prediction_text_bn': '✅ নিরাপদ লেনদেন।',
                'prediction_text_en': '✅ Transaction Safe & Approved.'
            })

    except Exception as e:
        return jsonify({
            'status': 'danger', 
            'prediction_text_bn': f'ত্রুটি: {str(e)}',
            'prediction_text_en': f'Error: {str(e)}'
        }), 400


if __name__ == '__main__':
    app.run(debug=True)
    
