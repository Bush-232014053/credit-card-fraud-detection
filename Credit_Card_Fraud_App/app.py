from flask import Flask, render_template, request, jsonify
# import joblib  # Uncomment this line if you are using a trained .pkl / .joblib ML model

app = Flask(__name__)

# Load your Machine Learning model here if available:
# model = joblib.load('model.pkl')


# 1. Landing / Home Page Route
@app.route('/')
def home():
    return render_template('index.html')


# 2. Main Dashboard Route
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')


# 3. Login Page Route
@app.route('/login')
def login():
    return render_template('login.html')


# 4. Register Page Route
@app.route('/register')
def register():
    return render_template('register.html')


# 5. AI Prediction Endpoint (Handles form submission from dashboard.html via AJAX)
@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Extract all 6 input features from dashboard.html form submission
        amount = float(request.form.get('Transaction_Amount', 0))
        time_since_last_tx = float(request.form.get('Time_Since_Last_Tx', 0))
        distance_from_last_tx = float(request.form.get('Distance_From_Last_Tx', 0))
        distance_from_home = float(request.form.get('Distance_From_Home', 0))
        daily_limit_used = float(request.form.get('Daily_Limit_Used', 0))
        card_age_days = float(request.form.get('Card_Age_Days', 0))

        # --- Option A: Prediction using a pre-trained ML Model ---
        # features = [[amount, time_since_last_tx, distance_from_last_tx, distance_from_home, daily_limit_used, card_age_days]]
        # prediction = model.predict(features)[0] # 1 = Fraud, 0 = Safe
        # is_fraud = (prediction == 1)

        # --- Option B: Demonstration Rule-Based Logic ---
        # Flags transaction as fraud if amount > $1000, daily limit > 80%, or distance from home > 200 km
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
