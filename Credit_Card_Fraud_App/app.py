import re
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'super_secret_fraudguard_key'  # Required for session management & flash alerts

# -------------------------------------------------------------
# Dummy User Database (Default Username/Email & Password)
# Default Login: "abc" or "abc@company.com"
# Default Password adhering to security rules: "Abc@123"
# -------------------------------------------------------------
users_db = {
    "abc@company.com": generate_password_hash("Abc@123"),
    "abc": generate_password_hash("Abc@123")  # Allows login using 'abc' username
}


# -------------------------------------------------------------
# Password Validation Function
# Policy Rules: Min 6 chars, >=1 Uppercase, >=1 Lowercase, >=1 Special Symbol
# -------------------------------------------------------------
def is_valid_password(password):
    # 1. Minimum 6 characters long
    if len(password) < 6:
        return False, "Password must be at least 6 characters long!"
    
    # 2. At least one uppercase letter (A-Z)
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter (A-Z)!"
    
    # 3. At least one lowercase letter (a-z)
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter (a-z)!"
    
    # 4. At least one special symbol (!@#$%^&* etc.)
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*)!"
    
    return True, "Valid Password"


# 1. Landing / Home Page Route
@app.route('/')
def home():
    return render_template('index.html')


# 2. Main Dashboard Route
@app.route('/dashboard')
def dashboard():
    # Redirect unauthenticated users to login page
    if 'user' not in session:
        flash('Please login first to access the dashboard.', 'warning')
        return redirect(url_for('login'))
    return render_template('dashboard.html')


# 3. Login Page Route (GET & POST)
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email_or_user = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Retrieve stored password hash for the given user
        stored_hash = users_db.get(email_or_user)

        # Validate username and hashed password
        if stored_hash and check_password_hash(stored_hash, password):
            session['user'] = email_or_user
            flash('Successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email/username or password!', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# 4. Register Page Route (GET & POST with Strong Password Enforcement)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        # Check if email is already registered
        if email in users_db:
            flash('This email is already registered!', 'warning')
            return redirect(url_for('register'))

        # Validate password strength against policy
        is_valid, msg = is_valid_password(password)
        if not is_valid:
            flash(msg, 'danger')
            return redirect(url_for('register'))

        # Save user with hashed password
        users_db[email] = generate_password_hash(password)
        flash('Registration successful! Please sign in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


# 5. Logout Route
@app.route('/logout')
def logout():
    session.pop('user', None)
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


# 6. AI Prediction Endpoint (Handles form submission from dashboard.html via AJAX)
@app.route('/predict', methods=['POST'])
def predict():
    try:
        amount = float(request.form.get('Transaction_Amount', 0))
        time_since_last_tx = float(request.form.get('Time_Since_Last_Tx', 0))
        distance_from_last_tx = float(request.form.get('Distance_From_Last_Tx', 0))
        distance_from_home = float(request.form.get('Distance_From_Home', 0))
        daily_limit_used = float(request.form.get('Daily_Limit_Used', 0))
        card_age_days = float(request.form.get('Card_Age_Days', 0))

        # Demonstration Rule-Based Logic
        is_fraud = (amount > 1000) or (daily_limit_used > 80) or (distance_from_home > 200)

        if is_fraud:
            return jsonify({
                'status': 'danger',
                'prediction_text': 'Fraud Alert Detected!'
            })
        else:
            return jsonify({
                'status': 'success',
                'prediction_text': 'Transaction Safe'
            })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'prediction_text': f"Server Error: {str(e)}"
        })


if __name__ == '__main__':
    app.run(debug=True)
    
